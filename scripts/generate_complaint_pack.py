"""
Generate complete complaint pack including:
1. Formal complaint templates for each regulatory body
2. Legal chronology of breaches with dates
3. Specific quotes with document references

This creates actionable documents for pursuing accountability.
"""
import sqlite3
import json
import os
from datetime import datetime
from collections import defaultdict
import re

# ============================================================================
# DATABASE CONNECTION
# ============================================================================

conn = sqlite3.connect('Phronesis/data/db/phronesis.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Load the audit report
with open('data/accountability_audit_report.json', 'r', encoding='utf-8') as f:
    audit_report = json.load(f)

# ============================================================================
# EXTRACT EVIDENCE WITH DOCUMENT REFERENCES
# ============================================================================

def extract_evidence_quotes():
    """Extract specific quotes with full document references."""
    
    print("Extracting evidence quotes with document references...")
    
    evidence_pack = {
        'police': [],
        'local_authority': [],
        'cafcass': [],
        'social_worker': [],
        'family_court': [],
        'media': []
    }
    
    # Key breach indicators to search for
    search_terms = {
        'police': [
            ('failure to investigate', 'PACE 1984; College of Policing APP'),
            ('not disclosed', 'CPIA 1996 - Disclosure duty'),
            ('ignored evidence', 'PACE 1984'),
            ('bail', 'PACE 1984 s.47ZA-ZL'),
        ],
        'local_authority': [
            ('threshold', 'Children Act 1989 s.31(2)'),
            ('no evidence of harm', 'Children Act 1989 s.31(2)'),
            ('didn\'t disclose', 'Working Together 2023; Re W (Children)'),
            ('disproportionate', 'Human Rights Act 1998; ECHR Article 8'),
            ('failed to inform', 'Duty of Candour'),
        ],
        'cafcass': [
            ('adopted', 'CJCS Act 2000 s.12'),
            ('agreed with', 'CAFCASS Operating Framework'),
            ('didn\'t see child', 'Children Act 1989 s.7'),
            ('guardian', 'FPR 2010 r.16.4'),
        ],
        'social_worker': [
            ('not what I said', 'HCPC Standards'),
            ('misquoted', 'HCPC Standards'),
            ('inaccurate', 'Working Together 2023'),
            ('failed to follow', 'HCPC Standards of Proficiency'),
        ],
        'family_court': [
            ('wasn\'t heard', 'HRA 1998; ECHR Article 6'),
            ('refused to consider', 'HRA 1998; ECHR Article 6'),
            ('no opportunity', 'HRA 1998; ECHR Article 6'),
            ('not enough time', 'FPR 2010 r.1.1'),
        ],
        'media': [
            ('documentary', 'Children Act 1989 s.97'),
            ('consent', 'Ofcom Broadcasting Code'),
            ('filmed', 'Contempt of Court Act 1981'),
        ]
    }
    
    for agency, terms in search_terms.items():
        for term, legal_basis in terms:
            cursor.execute("""
                SELECT c.claim_text, c.asserted_by, c.date_made, c.context,
                       d.filename, d.title, d.document_category, d.document_date
                FROM claims c
                LEFT JOIN documents d ON c.document_id = d.id
                WHERE LOWER(c.claim_text) LIKE ?
                LIMIT 10
            """, (f'%{term.lower()}%',))
            
            for row in cursor.fetchall():
                evidence_pack[agency].append({
                    'quote': row['claim_text'],
                    'author': row['asserted_by'],
                    'date': row['date_made'] or row['document_date'],
                    'document': row['filename'] or row['title'],
                    'document_category': row['document_category'],
                    'search_term': term,
                    'legal_basis': legal_basis
                })
    
    return evidence_pack

# ============================================================================
# BUILD LEGAL CHRONOLOGY
# ============================================================================

def build_legal_chronology():
    """Build chronology of breaches and key events."""
    
    print("Building legal chronology...")
    
    # Get all claims with dates
    cursor.execute("""
        SELECT c.claim_text, c.asserted_by, c.date_made, c.claim_type,
               d.filename, d.title, d.document_date, d.document_category
        FROM claims c
        LEFT JOIN documents d ON c.document_id = d.id
        WHERE c.date_made IS NOT NULL OR d.document_date IS NOT NULL
        ORDER BY COALESCE(c.date_made, d.document_date)
    """)
    
    dated_claims = cursor.fetchall()
    
    # Key events timeline
    timeline = [
        # 2021
        {'date': '2021', 'event': 'PE21P30644 - Original private law proceedings commence', 'type': 'PROCEEDINGS', 'case': 'PE21P30644'},
        
        # 2022
        {'date': '2022-04', 'event': 'Stephen Alderton texts about "Panama" - evidence of premeditation', 'type': 'EVIDENCE', 'case': 'CRIMINAL'},
        {'date': '2022-05', 'event': 'PE22P00090 - Cambridge Family Court proceedings', 'type': 'PROCEEDINGS', 'case': 'PE22P00090'},
        {'date': '2022-06', 'event': 'Stephen Alderton texts "Plan B" and "Independence Day"', 'type': 'EVIDENCE', 'case': 'CRIMINAL'},
        {'date': '2022', 'event': 'PE22P31058 - Further private law proceedings', 'type': 'PROCEEDINGS', 'case': 'PE22P31058'},
        
        # 2023 March - Critical Month
        {'date': '2023-03-27', 'event': 'Family Court hearing - CAFCASS recommends child NOT leave UK', 'type': 'CAFCASS_BREACH', 'case': 'PE22P31058'},
        {'date': '2023-03-29', 'event': 'MURDERS: Joshua and Gary Dunmore killed by Stephen Alderton', 'type': 'CRIME', 'case': 'CRIMINAL'},
        {'date': '2023-03-30', 'event': 'Paul & Samantha Stephen arrested for conspiracy to murder', 'type': 'ARREST', 'case': 'CRIMINAL'},
        {'date': '2023-03-31', 'event': 'Released NFA - POTENTIAL POLICE BREACH: Premature release?', 'type': 'POLICE_BREACH', 'case': 'CRIMINAL'},
        
        # 2023 April onwards
        {'date': '2023-04', 'event': 'PE23C50063 - Initial care application by Local Authority', 'type': 'PROCEEDINGS', 'case': 'PE23C50063'},
        {'date': '2023-05-12', 'event': 'Suspect status reinstated by DCI Dounias', 'type': 'POLICE', 'case': 'CRIMINAL'},
        {'date': '2023-06-07', 'event': 'Re-arrested, "no comment" interviews', 'type': 'ARREST', 'case': 'CRIMINAL'},
        {'date': '2023-06-09', 'event': 'PE23C50095 - Urgent ICO hearing HHJ Gordon-Saker', 'type': 'COURT_BREACH', 'case': 'PE23C50095'},
        {'date': '2023', 'event': 'PE23P30344 - New private law proceedings (Mandy Seamark)', 'type': 'PROCEEDINGS', 'case': 'PE23P30344'},
        
        # 2024
        {'date': '2024', 'event': 'CA-2024-001096 - Court of Appeal permission REFUSED', 'type': 'APPEAL_BREACH', 'case': 'CA-2024-001096'},
        {'date': '2024-07', 'event': 'PE23C50095 - Ongoing care proceedings', 'type': 'PROCEEDINGS', 'case': 'PE23C50095'},
        
        # 2025
        {'date': '2025-02-12', 'event': 'Criminal investigation: Final NFA - insufficient evidence', 'type': 'POLICE_OUTCOME', 'case': 'CRIMINAL'},
    ]
    
    # Add breaches from dated claims
    breach_keywords = {
        'POLICE_BREACH': ['police', 'arrest', 'bail', 'investigation', 'disclosure'],
        'LA_BREACH': ['local authority', 'social worker', 'threshold', 'harm'],
        'CAFCASS_BREACH': ['cafcass', 'guardian', 'section 7'],
        'COURT_BREACH': ['judge', 'court', 'hearing', 'order'],
    }
    
    for claim in dated_claims:
        date = claim['date_made'] or claim['document_date']
        if not date:
            continue
            
        text = (claim['claim_text'] or '').lower()
        
        for breach_type, keywords in breach_keywords.items():
            if any(kw in text for kw in keywords):
                # Check if it's actually a breach indicator
                breach_indicators = ['fail', 'didn\'t', 'refused', 'ignored', 'not disclosed', 'breach']
                if any(ind in text for ind in breach_indicators):
                    timeline.append({
                        'date': date,
                        'event': claim['claim_text'][:100] + '...',
                        'type': breach_type,
                        'document': claim['filename'] or claim['title'],
                        'author': claim['asserted_by']
                    })
    
    # Sort by date
    def parse_date(d):
        if not d:
            return '9999'
        return str(d)
    
    timeline.sort(key=lambda x: parse_date(x.get('date', '')))
    
    return timeline

# ============================================================================
# GENERATE COMPLAINT TEMPLATES
# ============================================================================

def generate_iopc_complaint(evidence):
    """Generate IOPC complaint template."""
    
    template = """
================================================================================
INDEPENDENT OFFICE FOR POLICE CONDUCT (IOPC)
FORMAL COMPLAINT
================================================================================

COMPLAINANT DETAILS
-------------------
Name: [YOUR NAME]
Address: [YOUR ADDRESS]
Contact: [YOUR CONTACT DETAILS]

DATE OF COMPLAINT: {date}

FORCE COMPLAINED ABOUT: Cambridgeshire Constabulary / Beds, Cambs & Herts Major Crime Unit

OFFICERS INVOLVED:
- DCI Katie Dounias (Senior Investigating Officer)
- DC 2072 Atkinson (Officer in Case)
- [Other officers as identified]

CASE REFERENCES:
- Operation Scan - Murder Investigation (Joshua and Gary Dunmore)
- URN: 35/KL/392/23
- Family Court: PE23C50095, PE21P30644, PE22P31058

================================================================================
GROUNDS OF COMPLAINT
================================================================================

I make this complaint pursuant to the Police Reform Act 2002 and the Police 
(Complaints and Misconduct) Regulations 2020.

1. FAILURE TO INVESTIGATE WITHOUT PREJUDICE
   Legal Basis: PACE 1984; College of Policing Authorised Professional Practice
   
   The investigation into the murders of Joshua and Gary Dunmore and the 
   subsequent conspiracy allegations against myself and my wife failed to 
   meet the standards required of an objective investigation.
   
   EVIDENCE:
   {police_evidence_1}

2. DISCLOSURE FAILURES
   Legal Basis: Criminal Procedure and Investigations Act 1996
   
   Material relevant to the investigation was not disclosed in accordance 
   with statutory requirements.
   
   EVIDENCE:
   {police_evidence_2}

3. PACE CODE C VIOLATIONS
   Legal Basis: Police and Criminal Evidence Act 1984, Code C
   
   The treatment during detention and interview did not comply with 
   PACE Code C requirements.
   
   EVIDENCE:
   {police_evidence_3}

================================================================================
DOCUMENTARY EVIDENCE ATTACHED
================================================================================
{evidence_list}

================================================================================
REMEDY SOUGHT
================================================================================
1. Full investigation into the conduct of officers named
2. Review of the investigation decisions
3. Disclosure of all material held
4. Disciplinary action where appropriate
5. Compensation for distress and impact on family proceedings

================================================================================
DECLARATION
================================================================================
I confirm that the information provided is true and accurate to the best of 
my knowledge. I understand that making a false statement may constitute an 
offence.

Signed: _______________________

Date: _______________________

================================================================================
SUBMIT TO:
IOPC
PO Box 473
Sale
M33 0BW
Email: enquiries@policeconduct.gov.uk
================================================================================
""".format(
        date=datetime.now().strftime('%d %B %Y'),
        police_evidence_1=format_evidence(evidence.get('police', [])[:3]),
        police_evidence_2=format_evidence([e for e in evidence.get('police', []) if 'disclos' in e.get('search_term', '').lower()][:3]),
        police_evidence_3=format_evidence([e for e in evidence.get('police', []) if 'pace' in e.get('legal_basis', '').lower()][:3]),
        evidence_list=format_evidence_list(evidence.get('police', []))
    )
    
    return template

def generate_lgsco_complaint(evidence):
    """Generate Local Government & Social Care Ombudsman complaint."""
    
    template = """
================================================================================
LOCAL GOVERNMENT AND SOCIAL CARE OMBUDSMAN (LGSCO)
FORMAL COMPLAINT
================================================================================

COMPLAINANT DETAILS
-------------------
Name: [YOUR NAME]
Address: [YOUR ADDRESS]
Contact: [YOUR CONTACT DETAILS]

DATE OF COMPLAINT: {date}

AUTHORITY COMPLAINED ABOUT: Cambridgeshire County Council
Department: Children's Services

CASE REFERENCES:
- PE23C50095 (Care Proceedings)
- PE23C50063 (Former Care Application)

================================================================================
PRELIMINARY REQUIREMENTS
================================================================================

☐ I confirm I have exhausted the Council's internal complaints procedure
☐ I attach copies of the Council's final response
☐ This complaint is made within 12 months of the matters complained of

================================================================================
GROUNDS OF COMPLAINT - MALADMINISTRATION
================================================================================

I complain that Cambridgeshire County Council's Children's Services has 
caused injustice through maladministration in its handling of care 
proceedings concerning my children.

1. FAILURE TO MEET SECTION 31 THRESHOLD
   Legal Basis: Children Act 1989 s.31(2)
   
   The Local Authority issued care proceedings without adequate evidence 
   that the threshold criteria were met.
   
   EVIDENCE:
   {la_evidence_1}

2. BREACH OF DUTY OF CANDOUR
   Legal Basis: Working Together 2023; Re W (Children) [2014]
   
   The Local Authority failed to present all relevant information to the 
   court, including material that undermined its case.
   
   EVIDENCE:
   {la_evidence_2}

3. DISPROPORTIONATE INTERFERENCE WITH ARTICLE 8 RIGHTS
   Legal Basis: Human Rights Act 1998; ECHR Article 8
   
   The Local Authority's actions constituted disproportionate interference 
   with our right to family life.
   
   EVIDENCE:
   {la_evidence_3}

4. FAILURE TO FOLLOW PRE-PROCEEDINGS PROTOCOL
   Legal Basis: Public Law Outline 2014; Practice Direction 12A
   
   [Detail if applicable]

================================================================================
INJUSTICE SUFFERED
================================================================================
- Separation from children
- Emotional distress
- Financial costs of legal proceedings
- Damage to family relationships
- Impact on children's welfare

================================================================================
REMEDY SOUGHT
================================================================================
1. Finding of maladministration
2. Apology from the Council
3. Review of social work practice
4. Compensation for injustice suffered
5. Training recommendations for staff

================================================================================
DOCUMENTARY EVIDENCE
================================================================================
{evidence_list}

================================================================================
DECLARATION
================================================================================
I confirm that the information provided is true and accurate to the best of 
my knowledge.

Signed: _______________________

Date: _______________________

================================================================================
SUBMIT TO:
Local Government and Social Care Ombudsman
PO Box 4771
Coventry
CV4 0EH
www.lgo.org.uk
================================================================================
""".format(
        date=datetime.now().strftime('%d %B %Y'),
        la_evidence_1=format_evidence([e for e in evidence.get('local_authority', []) if 'threshold' in e.get('search_term', '').lower()][:3]),
        la_evidence_2=format_evidence([e for e in evidence.get('local_authority', []) if 'disclose' in e.get('search_term', '').lower() or 'inform' in e.get('search_term', '').lower()][:3]),
        la_evidence_3=format_evidence([e for e in evidence.get('local_authority', []) if 'disproportionate' in e.get('search_term', '').lower()][:3]),
        evidence_list=format_evidence_list(evidence.get('local_authority', []))
    )
    
    return template

def generate_cafcass_complaint(evidence):
    """Generate CAFCASS complaint."""
    
    template = """
================================================================================
CAFCASS FORMAL COMPLAINT
================================================================================

COMPLAINANT DETAILS
-------------------
Name: [YOUR NAME]
Address: [YOUR ADDRESS]
Contact: [YOUR CONTACT DETAILS]

DATE OF COMPLAINT: {date}

CAFCASS OFFICER(S) COMPLAINED ABOUT:
- [Name of Children's Guardian]
- [Name of Family Court Adviser]

CASE REFERENCES:
- PE23C50095
- PE23P30344

================================================================================
GROUNDS OF COMPLAINT
================================================================================

I make this complaint under the CAFCASS complaints procedure regarding 
failures in the discharge of statutory duties.

1. FAILURE OF INDEPENDENCE AND IMPARTIALITY
   Legal Basis: Criminal Justice and Court Services Act 2000 s.12; 
                CAFCASS Operating Framework
   
   The CAFCASS officer(s) failed to act independently of the Local Authority 
   and adopted their position without independent analysis.
   
   EVIDENCE:
   {cafcass_evidence_1}

2. FAILURE TO PROPERLY ASCERTAIN CHILD'S WISHES
   Legal Basis: Children Act 1989 s.1(3)(a); UNCRC Article 12
   
   The child's wishes and feelings were not properly ascertained or 
   conveyed to the court.
   
   EVIDENCE:
   {cafcass_evidence_2}

3. INADEQUATE SECTION 7 REPORT
   Legal Basis: Children Act 1989 s.7
   
   The welfare report failed to meet required standards.
   
   EVIDENCE:
   {cafcass_evidence_3}

================================================================================
REMEDY SOUGHT
================================================================================
1. Investigation into the conduct of the named officer(s)
2. Review and revision of reports submitted to court
3. Apology
4. Training recommendations
5. Escalation to Parliamentary Ombudsman if not resolved

================================================================================
DOCUMENTARY EVIDENCE
================================================================================
{evidence_list}

Signed: _______________________

Date: _______________________

================================================================================
SUBMIT TO:
CAFCASS
3rd Floor, 21 Bloomsbury Street
London WC1B 3HF
complaints@cafcass.gov.uk
================================================================================
""".format(
        date=datetime.now().strftime('%d %B %Y'),
        cafcass_evidence_1=format_evidence([e for e in evidence.get('cafcass', []) if 'adopted' in e.get('search_term', '').lower() or 'agreed' in e.get('search_term', '').lower()][:3]),
        cafcass_evidence_2=format_evidence([e for e in evidence.get('cafcass', []) if 'child' in e.get('search_term', '').lower()][:3]),
        cafcass_evidence_3=format_evidence(evidence.get('cafcass', [])[:3]),
        evidence_list=format_evidence_list(evidence.get('cafcass', []))
    )
    
    return template

def generate_hcpc_referral(evidence):
    """Generate HCPC Fitness to Practise referral."""
    
    template = """
================================================================================
HEALTH AND CARE PROFESSIONS COUNCIL (HCPC)
FITNESS TO PRACTISE REFERRAL
================================================================================

REFERRER DETAILS
----------------
Name: [YOUR NAME]
Address: [YOUR ADDRESS]
Contact: [YOUR CONTACT DETAILS]

DATE OF REFERRAL: {date}

REGISTRANT DETAILS
------------------
Name: [SOCIAL WORKER NAME]
Registration Number: [IF KNOWN]
Employer: Cambridgeshire County Council

================================================================================
NATURE OF CONCERNS
================================================================================

I refer concerns about the fitness to practise of the above-named social 
worker on the following grounds:

1. FAILURE TO MEET STANDARDS OF PROFICIENCY
   HCPC Standard: Be able to practise safely and effectively within their 
                  scope of practice
   
   EVIDENCE:
   {sw_evidence_1}

2. INACCURATE RECORDING
   HCPC Standard: Be able to maintain records appropriately
   
   The social worker's records contain inaccuracies and misrepresentations.
   
   EVIDENCE:
   {sw_evidence_2}

3. FAILURE TO PRACTISE WITHIN LEGAL AND ETHICAL BOUNDARIES
   HCPC Standard: Understand the importance of and be able to maintain 
                  confidentiality; Be aware of current legislation
   
   EVIDENCE:
   {sw_evidence_3}

================================================================================
IMPACT
================================================================================
These failures have resulted in:
- Separation of family
- Inaccurate information being presented to court
- Harm to children's welfare
- Injustice in legal proceedings

================================================================================
DOCUMENTARY EVIDENCE
================================================================================
{evidence_list}

================================================================================
DECLARATION
================================================================================
I confirm that the information provided is true and accurate. I understand 
that the HCPC may share this referral with the registrant.

Signed: _______________________

Date: _______________________

================================================================================
SUBMIT TO:
HCPC Fitness to Practise Department
Park House
184 Kennington Park Road
London SE11 4BU
ftp@hcpc-uk.org
================================================================================
""".format(
        date=datetime.now().strftime('%d %B %Y'),
        sw_evidence_1=format_evidence([e for e in evidence.get('social_worker', []) if 'failed' in e.get('search_term', '').lower()][:3]),
        sw_evidence_2=format_evidence([e for e in evidence.get('social_worker', []) if 'said' in e.get('search_term', '').lower() or 'inaccurate' in e.get('search_term', '').lower()][:3]),
        sw_evidence_3=format_evidence(evidence.get('social_worker', [])[:3]),
        evidence_list=format_evidence_list(evidence.get('social_worker', []))
    )
    
    return template

def generate_ofcom_complaint(evidence):
    """Generate Ofcom complaint about Channel 4."""
    
    template = """
================================================================================
OFCOM BROADCASTING STANDARDS COMPLAINT
================================================================================

COMPLAINANT DETAILS
-------------------
Name: [YOUR NAME]
Address: [YOUR ADDRESS]
Contact: [YOUR CONTACT DETAILS]

DATE OF COMPLAINT: {date}

BROADCASTER: Channel 4
PROGRAMME: 24 Hours in Police Custody [or specific programme name]
TRANSMISSION DATE: [DATE]

================================================================================
GROUNDS OF COMPLAINT
================================================================================

I make this complaint under the Ofcom Broadcasting Code regarding the 
above programme.

1. SECTION 97 CHILDREN ACT 1989 - IDENTIFICATION OF CHILDREN
   
   The programme risks identifying children who are subject to family 
   court proceedings, contrary to s.97 Children Act 1989.
   
   EVIDENCE:
   {media_evidence_1}

2. OFCOM CODE SECTION 7 - FAIRNESS
   
   The programme treats contributors unfairly.
   
   EVIDENCE:
   {media_evidence_2}

3. OFCOM CODE SECTION 8 - PRIVACY
   
   The programme infringes privacy in a manner not warranted.
   
   EVIDENCE:
   {media_evidence_3}

4. CONSENT ISSUES
   
   Consent was not properly obtained or was obtained under circumstances 
   that vitiate it.
   
   EVIDENCE:
   {media_evidence_4}

================================================================================
REMEDY SOUGHT
================================================================================
1. Finding of Code breach
2. Order not to broadcast/re-broadcast without edits
3. Sanction against broadcaster
4. Apology/correction

================================================================================
DOCUMENTARY EVIDENCE
================================================================================
{evidence_list}

Signed: _______________________

Date: _______________________

================================================================================
SUBMIT TO:
Ofcom
Riverside House
2a Southwark Bridge Road
London SE1 9HA
www.ofcom.org.uk/complaints
================================================================================
""".format(
        date=datetime.now().strftime('%d %B %Y'),
        media_evidence_1=format_evidence([e for e in evidence.get('media', []) if 'documentary' in e.get('search_term', '').lower() or 'identif' in e.get('search_term', '').lower()][:2]),
        media_evidence_2=format_evidence(evidence.get('media', [])[:2]),
        media_evidence_3=format_evidence(evidence.get('media', [])[:2]),
        media_evidence_4=format_evidence([e for e in evidence.get('media', []) if 'consent' in e.get('search_term', '').lower()][:2]),
        evidence_list=format_evidence_list(evidence.get('media', []))
    )
    
    return template

def format_evidence(evidence_list):
    """Format evidence items for inclusion in template."""
    if not evidence_list:
        return "   [No specific evidence extracted - review case files]"
    
    formatted = []
    for e in evidence_list[:3]:
        formatted.append(f"""
   Document: {e.get('document', 'Unknown')}
   Date: {e.get('date', 'Unknown')}
   Author: {e.get('author', 'Unknown')}
   Quote: "{e.get('quote', '')[:150]}..."
   Legal Basis: {e.get('legal_basis', '')}
""")
    return '\n'.join(formatted)

def format_evidence_list(evidence_list):
    """Format list of documentary evidence."""
    if not evidence_list:
        return "- Case bundle documents\n- Court orders\n- Professional reports"
    
    docs = list(set(e.get('document', 'Unknown') for e in evidence_list))[:10]
    return '\n'.join(f"- {doc}" for doc in docs)

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    print("="*70)
    print("GENERATING COMPLETE COMPLAINT PACK")
    print("="*70)
    
    # Create output directory
    os.makedirs('data/complaints', exist_ok=True)
    
    # Extract evidence
    evidence = extract_evidence_quotes()
    
    # Save evidence pack
    with open('data/complaints/evidence_pack.json', 'w', encoding='utf-8') as f:
        json.dump(evidence, f, indent=2, ensure_ascii=False, default=str)
    print("\n✓ Evidence pack saved to data/complaints/evidence_pack.json")
    
    # Build chronology
    chronology = build_legal_chronology()
    
    # Save chronology
    with open('data/complaints/legal_chronology.json', 'w', encoding='utf-8') as f:
        json.dump(chronology, f, indent=2, ensure_ascii=False, default=str)
    
    # Also save as readable text
    with open('data/complaints/legal_chronology.txt', 'w', encoding='utf-8') as f:
        f.write("LEGAL CHRONOLOGY OF BREACHES\n")
        f.write("="*70 + "\n\n")
        for event in chronology[:100]:  # First 100 events
            f.write(f"{event.get('date', 'Unknown'):15} | {event.get('type', ''):20} | {event.get('event', '')[:60]}\n")
    print("✓ Legal chronology saved to data/complaints/legal_chronology.txt")
    
    # Generate complaint templates
    complaints = {
        'IOPC_complaint.txt': generate_iopc_complaint(evidence),
        'LGSCO_complaint.txt': generate_lgsco_complaint(evidence),
        'CAFCASS_complaint.txt': generate_cafcass_complaint(evidence),
        'HCPC_referral.txt': generate_hcpc_referral(evidence),
        'Ofcom_complaint.txt': generate_ofcom_complaint(evidence),
    }
    
    for filename, content in complaints.items():
        filepath = f'data/complaints/{filename}'
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✓ {filename} saved")
    
    # Summary
    print("\n" + "="*70)
    print("COMPLAINT PACK COMPLETE")
    print("="*70)
    print(f"""
Files generated in data/complaints/:

COMPLAINT TEMPLATES:
  1. IOPC_complaint.txt       - Police misconduct (IOPC)
  2. LGSCO_complaint.txt      - Local Authority (Ombudsman)
  3. CAFCASS_complaint.txt    - CAFCASS complaints
  4. HCPC_referral.txt        - Social worker (HCPC)
  5. Ofcom_complaint.txt      - Channel 4 (Ofcom)

SUPPORTING DOCUMENTS:
  - evidence_pack.json        - All extracted quotes with references
  - legal_chronology.txt      - Timeline of breaches
  - legal_chronology.json     - Machine-readable timeline

EVIDENCE EXTRACTED:
  - Police:          {police_count} quotes
  - Local Authority: {la_count} quotes
  - CAFCASS:         {cafcass_count} quotes
  - Social Worker:   {sw_count} quotes
  - Media:           {media_count} quotes
  - Family Court:    {court_count} quotes

NEXT STEPS:
1. Review each complaint template
2. Add your personal details
3. Attach supporting documents from case files
4. Submit to relevant bodies
5. Keep copies of everything submitted
""".format(
        police_count=len(evidence.get('police', [])),
        la_count=len(evidence.get('local_authority', [])),
        cafcass_count=len(evidence.get('cafcass', [])),
        sw_count=len(evidence.get('social_worker', [])),
        media_count=len(evidence.get('media', [])),
        court_count=len(evidence.get('family_court', []))
    ))
    
    conn.close()

if __name__ == "__main__":
    main()

