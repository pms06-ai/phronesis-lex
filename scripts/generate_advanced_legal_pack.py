"""
Generate advanced legal pack including:
1. Enhanced evidence extraction with specific quotes
2. Witness statement template
3. Subject Access Request (SAR) templates for all agencies
"""
import sqlite3
import json
import os
from datetime import datetime
from collections import defaultdict

# Database connection
conn = sqlite3.connect('Phronesis/data/db/phronesis.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

os.makedirs('data/complaints', exist_ok=True)

print("="*70)
print("GENERATING ADVANCED LEGAL PACK")
print("="*70)

# ============================================================================
# 1. ENHANCED EVIDENCE EXTRACTION
# ============================================================================

def extract_detailed_evidence():
    """Extract comprehensive evidence with full document references."""
    
    print("\n[1/3] Extracting detailed evidence...")
    
    evidence_sections = {}
    
    # Police evidence - specific searches
    police_queries = [
        ("Disclosure failures", "not disclosed OR late disclosure OR withheld OR failed to provide"),
        ("Investigation failures", "failure to investigate OR ignored evidence OR selective"),
        ("Bail issues", "bail OR custody OR arrest"),
        ("PACE violations", "interview OR caution OR solicitor"),
        ("Murder investigation", "murder OR conspiracy OR Operation Scan OR Alderton"),
    ]
    
    evidence_sections['police'] = []
    for category, search in police_queries:
        cursor.execute("""
            SELECT c.claim_text, c.asserted_by, c.date_made, c.context,
                   d.filename, d.title, d.document_date, d.document_category,
                   c.page_number
            FROM claims c
            LEFT JOIN documents d ON c.document_id = d.id
            WHERE c.claim_text LIKE ? OR c.claim_text LIKE ? OR c.claim_text LIKE ?
            LIMIT 15
        """, (f'%{search.split(" OR ")[0]}%', 
              f'%{search.split(" OR ")[1] if " OR " in search else search}%',
              f'%{search.split(" OR ")[2] if search.count(" OR ") >= 2 else search}%'))
        
        for row in cursor.fetchall():
            evidence_sections['police'].append({
                'category': category,
                'quote': row['claim_text'],
                'author': row['asserted_by'],
                'date': row['date_made'] or row['document_date'],
                'document': row['filename'] or row['title'],
                'page': row['page_number'],
                'doc_category': row['document_category']
            })
    
    # Local Authority evidence
    la_queries = [
        ("Threshold not met", "threshold OR significant harm OR no evidence of harm"),
        ("Duty of candour", "didn't disclose OR withheld OR failed to inform OR misleading"),
        ("Article 8 violations", "disproportionate OR unnecessary OR alternatives"),
        ("Care plan issues", "care plan OR placement OR foster"),
    ]
    
    evidence_sections['local_authority'] = []
    for category, search in la_queries:
        terms = search.split(" OR ")
        for term in terms[:3]:
            cursor.execute("""
                SELECT c.claim_text, c.asserted_by, c.date_made,
                       d.filename, d.title, d.document_date
                FROM claims c
                LEFT JOIN documents d ON c.document_id = d.id
                WHERE LOWER(c.claim_text) LIKE ?
                LIMIT 10
            """, (f'%{term.lower()}%',))
            
            for row in cursor.fetchall():
                evidence_sections['local_authority'].append({
                    'category': category,
                    'quote': row['claim_text'],
                    'author': row['asserted_by'],
                    'date': row['date_made'] or row['document_date'],
                    'document': row['filename'] or row['title']
                })
    
    # CAFCASS evidence
    cursor.execute("""
        SELECT c.claim_text, c.asserted_by, c.date_made,
               d.filename, d.title, d.document_date
        FROM claims c
        LEFT JOIN documents d ON c.document_id = d.id
        WHERE LOWER(c.claim_text) LIKE '%cafcass%' 
           OR LOWER(c.claim_text) LIKE '%guardian%'
           OR LOWER(c.claim_text) LIKE '%section 7%'
        LIMIT 30
    """)
    evidence_sections['cafcass'] = [dict(row) for row in cursor.fetchall()]
    
    # Social worker evidence
    cursor.execute("""
        SELECT c.claim_text, c.asserted_by, c.date_made,
               d.filename, d.title, d.document_date
        FROM claims c
        LEFT JOIN documents d ON c.document_id = d.id
        WHERE LOWER(c.claim_text) LIKE '%social worker%' 
           OR LOWER(c.claim_text) LIKE '%assessment%'
           OR LOWER(c.claim_text) LIKE '%not what%said%'
           OR LOWER(c.claim_text) LIKE '%inaccurate%'
        LIMIT 30
    """)
    evidence_sections['social_worker'] = [dict(row) for row in cursor.fetchall()]
    
    # Court/procedural evidence
    cursor.execute("""
        SELECT c.claim_text, c.asserted_by, c.date_made,
               d.filename, d.title, d.document_date
        FROM claims c
        LEFT JOIN documents d ON c.document_id = d.id
        WHERE LOWER(c.claim_text) LIKE '%was not heard%' 
           OR LOWER(c.claim_text) LIKE '%refused%'
           OR LOWER(c.claim_text) LIKE '%no opportunity%'
           OR LOWER(c.claim_text) LIKE '%fair%'
        LIMIT 30
    """)
    evidence_sections['court'] = [dict(row) for row in cursor.fetchall()]
    
    # Save enhanced evidence
    with open('data/complaints/detailed_evidence.json', 'w', encoding='utf-8') as f:
        json.dump(evidence_sections, f, indent=2, ensure_ascii=False, default=str)
    
    # Create readable evidence document
    with open('data/complaints/EVIDENCE_SCHEDULE.txt', 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("SCHEDULE OF EVIDENCE\n")
        f.write("Case: PE23C50095 - JFD vs SJS Family Proceedings\n")
        f.write("="*80 + "\n\n")
        
        for agency, items in evidence_sections.items():
            f.write(f"\n{'='*80}\n")
            f.write(f"{agency.upper().replace('_', ' ')} - EVIDENCE\n")
            f.write("="*80 + "\n")
            
            # Group by category if available
            by_category = defaultdict(list)
            for item in items:
                cat = item.get('category', 'General')
                by_category[cat].append(item)
            
            for category, cat_items in by_category.items():
                f.write(f"\n{category}\n")
                f.write("-"*40 + "\n")
                
                for i, item in enumerate(cat_items[:10], 1):
                    quote = item.get('claim_text') or item.get('quote', '')
                    f.write(f"\n{i}. Document: {item.get('document') or item.get('filename') or 'Unknown'}\n")
                    f.write(f"   Date: {item.get('date') or item.get('document_date') or 'Unknown'}\n")
                    f.write(f"   Author: {item.get('author') or item.get('asserted_by') or 'Unknown'}\n")
                    f.write(f"   Quote: \"{quote[:200]}{'...' if len(quote) > 200 else ''}\"\n")
    
    print(f"   ✓ Evidence schedule saved")
    return evidence_sections

# ============================================================================
# 2. WITNESS STATEMENT TEMPLATE
# ============================================================================

def generate_witness_statement():
    """Generate comprehensive witness statement template."""
    
    print("\n[2/3] Generating witness statement template...")
    
    # Get key facts from database
    cursor.execute("""
        SELECT claim_text, date_made, asserted_by 
        FROM claims 
        WHERE asserted_by LIKE '%stephen%' OR asserted_by LIKE '%mother%' OR asserted_by LIKE '%father%'
        ORDER BY date_made
        LIMIT 50
    """)
    personal_claims = cursor.fetchall()
    
    template = """
================================================================================
WITNESS STATEMENT

IN THE FAMILY COURT                                    Case No: PE23C50095
AT PETERBOROUGH                                        
                                                       
IN THE MATTER OF THE CHILDREN ACT 1989
AND IN THE MATTER OF [CHILD'S INITIALS]

================================================================================

I, [FULL NAME], of [ADDRESS], WILL SAY AS FOLLOWS:

1. INTRODUCTION
-------------------------------------------------------------------------------

1.1  I am the [Mother/Father] of [Child's name/initials], born [DOB]. I make 
     this statement in support of [purpose - e.g., "my application to 
     discharge the care order" / "in opposition to the Local Authority's 
     application"].

1.2  The facts stated in this witness statement are within my own knowledge 
     and are true. Where I refer to information provided by others, I identify 
     the source and believe that information to be true.

1.3  I have been involved in legal proceedings concerning my children since 
     [2021]. The relevant case numbers are:
     
     - PE21P30644 (Private Law, 2021)
     - PE22P00090 (Private Law, May 2022)
     - PE22P31058 (Private Law, 2022)
     - PE23C50063 (Public Law, 2023)
     - PE23C50095 (Public Law, Current)
     - PE23P30344 (Private Law, 2023)
     - CA-2024-001096 (Court of Appeal, 2024)

2. BACKGROUND
-------------------------------------------------------------------------------

2.1  [Describe family background]

2.2  [Describe relationship with other parent - Note: Samantha and Joshua were never married]

2.3  [Describe circumstances leading to proceedings]

3. THE EVENTS OF MARCH 2023
-------------------------------------------------------------------------------

3.1  On 27th March 2023, there was an interim hearing in the Family Court 
     regarding child arrangements. The CAFCASS report recommended that 
     [Child] should not be removed from the UK whilst proceedings were 
     in place.

3.2  On 29th March 2023, my father, Stephen Alderton, shot and killed 
     Joshua Dunmore and Gary Dunmore. I want to make absolutely clear:
     
     (a) I had no knowledge that my father intended to harm anyone
     (b) I did not conspire with my father or anyone else
     (c) I was as shocked as anyone by these terrible events

3.3  On 30th March 2023, at approximately 00:35 hours, my husband and I 
     were arrested at [location] on suspicion of conspiracy to murder.

3.4  On 31st March 2023, we were released with No Further Action.

3.5  On 12th May 2023, DCI Katie Dounias wrote to advise that our suspect 
     status had been reinstated.

3.6  On 7th June 2023, we were re-arrested and interviewed. We gave "no 
     comment" interviews on legal advice.

3.7  On 12th February 2025, after almost two years of investigation, we 
     received notification of No Further Action. The police concluded there 
     was "insufficient evidence to provide a realistic prospect of conviction."

4. MY CONCERNS ABOUT THE PROCEEDINGS
-------------------------------------------------------------------------------

4.1  POLICE INVESTIGATION
     I am concerned that the police investigation was not conducted fairly:
     
     (a) [Specific concern 1]
     (b) [Specific concern 2]
     (c) [Specific concern 3]

4.2  LOCAL AUTHORITY CONDUCT
     I am concerned that the Local Authority:
     
     (a) Failed to disclose relevant material
     (b) Presented a one-sided case to the court
     (c) Did not adequately evidence the threshold criteria
     (d) [Other concerns]

4.3  CAFCASS
     I am concerned that CAFCASS:
     
     (a) Did not act independently of the Local Authority
     (b) [Other concerns]

4.4  COURT PROCEEDINGS
     I am concerned about procedural fairness:
     
     (a) [Specific concerns about hearings]
     (b) [Concerns about opportunity to be heard]

5. THE IMPACT ON MY FAMILY
-------------------------------------------------------------------------------

5.1  [Describe impact on you]

5.2  [Describe impact on children]

5.3  [Describe impact on wider family]

6. WHAT I SEEK FROM THE COURT
-------------------------------------------------------------------------------

6.1  [State what orders you are seeking]

6.2  [State why these orders are in the children's best interests]

7. STATEMENT OF TRUTH
-------------------------------------------------------------------------------

I believe that the facts stated in this witness statement are true. I 
understand that proceedings for contempt of court may be brought against 
anyone who makes, or causes to be made, a false statement in a document 
verified by a statement of truth without an honest belief in its truth.

Signed: _________________________________

Full Name: [PRINT NAME]

Date: {date}

================================================================================
NOTES FOR COMPLETION:
================================================================================

1. Replace all items in [brackets] with your specific information
2. Be factual and avoid emotional language
3. Refer to documents by their exhibit numbers
4. Keep paragraphs short and numbered for easy reference
5. Have a solicitor review before filing
6. Keep a signed copy for your records

================================================================================
""".format(date=datetime.now().strftime('%d %B %Y'))
    
    with open('data/complaints/WITNESS_STATEMENT_TEMPLATE.txt', 'w', encoding='utf-8') as f:
        f.write(template)
    
    print("   ✓ Witness statement template saved")

# ============================================================================
# 3. SUBJECT ACCESS REQUEST TEMPLATES
# ============================================================================

def generate_sar_templates():
    """Generate Subject Access Request templates for all agencies."""
    
    print("\n[3/3] Generating Subject Access Request templates...")
    
    # Police SAR
    police_sar = """
================================================================================
SUBJECT ACCESS REQUEST
CAMBRIDGESHIRE CONSTABULARY
================================================================================

To: Data Protection Officer
    Cambridgeshire Constabulary
    Police Headquarters
    Hinchingbrooke Park
    Huntingdon
    PE29 6NP
    
    Email: dataprotection@cambs.police.uk

Date: {date}

SUBJECT ACCESS REQUEST UNDER UK GDPR ARTICLE 15 AND DATA PROTECTION ACT 2018

Dear Sir/Madam,

I am writing to make a Subject Access Request under Article 15 of the UK 
General Data Protection Regulation and the Data Protection Act 2018.

APPLICANT DETAILS
-----------------
Full Name: [YOUR FULL NAME]
Date of Birth: [YOUR DOB]
Address: [YOUR CURRENT ADDRESS]
Previous Addresses (last 5 years): [LIST]

IDENTIFICATION
--------------
I enclose copies of the following identification documents:
☐ Passport / Driving Licence (photo ID)
☐ Utility bill / Bank statement (proof of address)

INFORMATION REQUESTED
---------------------
I request copies of ALL personal data held about me, including but not 
limited to:

1. OPERATION SCAN (Murder Investigation)
   - URN: 35/KL/392/23
   - All intelligence reports mentioning me
   - All witness statements mentioning me
   - Interview recordings and transcripts
   - Custody records
   - Decision logs (charging decisions, NFA decisions)
   - Disclosure schedules
   - Communications about me (internal and external)
   - Risk assessments

2. POLICE NATIONAL COMPUTER (PNC) RECORDS
   - Any entries relating to me
   - Arrest records
   - Bail records

3. INTELLIGENCE SYSTEMS
   - Any intelligence entries
   - Any markers or flags

4. COMMUNICATIONS
   - Any correspondence with other agencies about me
   - Any correspondence with the Crown Prosecution Service
   - Any correspondence with the Family Court

5. BODY WORN VIDEO
   - Any footage featuring me

6. OTHER RECORDS
   - Any other records containing my personal data

THIRD PARTY DATA
----------------
I understand that third party data may need to be redacted. However, I 
request that you provide as much information as possible, and that any 
redactions are clearly marked with the exemption relied upon.

RESPONSE TIMEFRAME
------------------
I understand you must respond within one calendar month of receiving this 
request, or provide a valid reason for extension.

Please acknowledge receipt of this request within 5 working days.

Yours faithfully,

[SIGNATURE]
[PRINT NAME]

Enclosures:
- Copy of photo ID
- Copy of proof of address

================================================================================
""".format(date=datetime.now().strftime('%d %B %Y'))

    # Local Authority SAR
    la_sar = """
================================================================================
SUBJECT ACCESS REQUEST
CAMBRIDGESHIRE COUNTY COUNCIL - CHILDREN'S SERVICES
================================================================================

To: Data Protection Officer
    Cambridgeshire County Council
    Box No. CC1206
    Castle Court
    Castle Hill
    Cambridge
    CB3 0AP
    
    Email: dataprotection@cambridgeshire.gov.uk

Date: {date}

SUBJECT ACCESS REQUEST UNDER UK GDPR ARTICLE 15 AND DATA PROTECTION ACT 2018

Dear Sir/Madam,

I am writing to make a Subject Access Request under Article 15 of the UK 
General Data Protection Regulation and the Data Protection Act 2018.

APPLICANT DETAILS
-----------------
Full Name: [YOUR FULL NAME]
Date of Birth: [YOUR DOB]
Address: [YOUR CURRENT ADDRESS]
Children's Names/DOBs: [CHILDREN'S DETAILS]

Case References:
- PE23C50095 (Care Proceedings)
- PE23C50063 (Former Care Application)
- [Any other LA reference numbers]

IDENTIFICATION
--------------
I enclose copies of identification documents as specified in your SAR process.

INFORMATION REQUESTED
---------------------
I request copies of ALL personal data held about me and my children, 
including but not limited to:

1. CHILDREN'S SOCIAL CARE RECORDS
   - All case notes and chronologies
   - All assessments (initial, core, s.47, parenting)
   - All care plans
   - All case conference minutes
   - All strategy meeting minutes
   - All supervision notes mentioning me/my children
   - All management decisions and authorizations

2. CORRESPONDENCE
   - All internal emails about me/my family
   - All correspondence with other agencies (Police, CAFCASS, Health)
   - All correspondence with my legal representatives
   - All letters sent to me

3. COURT DOCUMENTS
   - All statements filed by the Local Authority
   - All reports prepared for court
   - All position statements
   - All threshold documents and drafts

4. LEGAL SERVICES RECORDS
   - All advice given to Children's Services about my case
   - All legal planning meeting minutes

5. COMPLAINTS RECORDS
   - Any complaints made by me or about me
   - Complaint investigation records

6. ELECTRONIC RECORDS
   - All entries on MOSAIC/Liquid Logic or equivalent system
   - All uploaded documents

CHILDREN'S RECORDS
------------------
I also request, as person with parental responsibility, access to my 
children's records. I understand there may be exemptions applied but 
request maximum disclosure.

RESPONSE TIMEFRAME
------------------
Please respond within one calendar month as required by law.

Yours faithfully,

[SIGNATURE]
[PRINT NAME]

================================================================================
""".format(date=datetime.now().strftime('%d %B %Y'))

    # CAFCASS SAR
    cafcass_sar = """
================================================================================
SUBJECT ACCESS REQUEST
CAFCASS
================================================================================

To: Data Protection Officer
    CAFCASS
    3rd Floor
    21 Bloomsbury Street
    London
    WC1B 3HF
    
    Email: dataprotection@cafcass.gov.uk

Date: {date}

SUBJECT ACCESS REQUEST UNDER UK GDPR ARTICLE 15 AND DATA PROTECTION ACT 2018

Dear Sir/Madam,

I am making a Subject Access Request for all personal data held about me.

APPLICANT DETAILS
-----------------
Full Name: [YOUR FULL NAME]
Date of Birth: [YOUR DOB]
Address: [YOUR CURRENT ADDRESS]

Case References:
- PE23C50095
- PE23P30344
- PE21P30644
- PE22P31058

Children's Guardians/FCAs involved: [NAMES IF KNOWN]

INFORMATION REQUESTED
---------------------
I request all personal data including:

1. CASE RECORDS
   - All Section 7 reports (drafts and final)
   - All Guardian reports
   - All case notes and chronologies
   - All analysis documents

2. SAFEGUARDING CHECKS
   - All checks undertaken and responses received
   - All referrals made

3. INTERNAL COMMUNICATIONS
   - All emails mentioning me
   - All internal consultations
   - All supervision notes

4. EXTERNAL COMMUNICATIONS
   - Correspondence with the court
   - Correspondence with Local Authority
   - Correspondence with other parties

5. RECORDINGS
   - Any recordings of meetings or interviews

Yours faithfully,

[SIGNATURE]
[PRINT NAME]

================================================================================
""".format(date=datetime.now().strftime('%d %B %Y'))

    # Court SAR
    court_sar = """
================================================================================
SUBJECT ACCESS REQUEST
HM COURTS & TRIBUNALS SERVICE
================================================================================

To: Data Protection Officer
    HMCTS
    102 Petty France
    London
    SW1H 9AJ
    
    Email: data.access@justice.gov.uk

Date: {date}

SUBJECT ACCESS REQUEST UNDER UK GDPR ARTICLE 15 AND DATA PROTECTION ACT 2018

Dear Sir/Madam,

I make this Subject Access Request for all personal data held about me.

APPLICANT DETAILS
-----------------
Full Name: [YOUR FULL NAME]
Date of Birth: [YOUR DOB]
Address: [YOUR CURRENT ADDRESS]

Court: Family Court at Peterborough
Case Numbers:
- PE23C50095
- PE21P30644
- PE22P31058
- PE22P00090
- PE23C50063
- PE23P30344
- CA-2024-001096

INFORMATION REQUESTED
---------------------
I request all personal data including:

1. CASE FILES
   - All documents on the court file for each case
   - All orders made (including draft orders)
   - All directions

2. ADMINISTRATIVE RECORDS
   - All case management notes
   - All listing notes
   - Any judge's notes (where disclosable)

3. CORRESPONDENCE
   - All correspondence with parties
   - All correspondence about the case

4. AUDIO RECORDINGS
   - All recordings of hearings (where made)

5. APPEAL RECORDS
   - All papers relating to CA-2024-001096

Yours faithfully,

[SIGNATURE]
[PRINT NAME]

================================================================================
""".format(date=datetime.now().strftime('%d %B %Y'))

    # Channel 4 SAR
    channel4_sar = """
================================================================================
SUBJECT ACCESS REQUEST
CHANNEL 4 / [PRODUCTION COMPANY]
================================================================================

To: Data Protection Officer
    Channel Four Television Corporation
    124 Horseferry Road
    London
    SW1P 2TX
    
    Email: dpo@channel4.co.uk

AND (if applicable)

To: Data Protection Officer
    [PRODUCTION COMPANY NAME]
    [ADDRESS]

Date: {date}

SUBJECT ACCESS REQUEST UNDER UK GDPR ARTICLE 15 AND DATA PROTECTION ACT 2018

Dear Sir/Madam,

I am making a Subject Access Request for all personal data held about me 
in connection with the programme "24 Hours in Police Custody" or any other 
production relating to Operation Scan or the Dunmore murders.

APPLICANT DETAILS
-----------------
Full Name: [YOUR FULL NAME]
Date of Birth: [YOUR DOB]
Address: [YOUR CURRENT ADDRESS]

INFORMATION REQUESTED
---------------------
I request all personal data including:

1. FOOTAGE
   - All filmed footage featuring me
   - All audio recordings of me
   - Any images of me

2. EDITORIAL MATERIALS
   - All scripts, treatments, running orders mentioning me
   - All research notes about me
   - All editorial decision logs about me

3. CONSENT RECORDS
   - Any consent forms (or records of absence of consent)
   - Any legal advice about consent/identification

4. CORRESPONDENCE
   - All correspondence with Cambridgeshire Police about me
   - All correspondence with anyone about me
   - All internal communications about me

5. OFCOM/LEGAL
   - Any legal advice about broadcasting restrictions
   - Any risk assessments about my identification

LEGAL CONTEXT
-------------
For context, I am a party to ongoing Family Court proceedings (PE23C50095) 
and the children who are the subject of those proceedings are protected by 
s.97 Children Act 1989.

I am concerned about potential identification of myself and the children.

Yours faithfully,

[SIGNATURE]
[PRINT NAME]

================================================================================
""".format(date=datetime.now().strftime('%d %B %Y'))

    # Save all SARs
    sars = {
        'SAR_Police.txt': police_sar,
        'SAR_LocalAuthority.txt': la_sar,
        'SAR_CAFCASS.txt': cafcass_sar,
        'SAR_Court.txt': court_sar,
        'SAR_Channel4.txt': channel4_sar,
    }
    
    for filename, content in sars.items():
        with open(f'data/complaints/{filename}', 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"   ✓ {filename} saved")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    # 1. Extract detailed evidence
    evidence = extract_detailed_evidence()
    
    # 2. Generate witness statement
    generate_witness_statement()
    
    # 3. Generate SAR templates
    generate_sar_templates()
    
    print("\n" + "="*70)
    print("ADVANCED LEGAL PACK COMPLETE")
    print("="*70)
    print("""
FILES GENERATED:

EVIDENCE:
  - detailed_evidence.json      (Machine-readable evidence)
  - EVIDENCE_SCHEDULE.txt       (Formatted evidence schedule)

WITNESS STATEMENT:
  - WITNESS_STATEMENT_TEMPLATE.txt

SUBJECT ACCESS REQUESTS:
  - SAR_Police.txt              (Cambridgeshire Constabulary)
  - SAR_LocalAuthority.txt      (Cambridgeshire County Council)
  - SAR_CAFCASS.txt             (CAFCASS)
  - SAR_Court.txt               (HMCTS)
  - SAR_Channel4.txt            (Channel 4 / Production Company)

TOTAL FILES IN data/complaints/: 
""")
    
    # List all files
    for f in sorted(os.listdir('data/complaints')):
        print(f"  - {f}")
    
    print("""
NEXT STEPS:
1. Submit SARs to all agencies (30-day response time)
2. Review data received against evidence schedule
3. Update complaint templates with SAR disclosures
4. File complaints with enhanced evidence
""")
    
    conn.close()

if __name__ == "__main__":
    main()

