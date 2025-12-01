"""
Run the full accountability audit across all agencies.
"""
import sys
import os
import re
import sqlite3
import json
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum
from collections import defaultdict

# ============================================================================
# STATUTORY FRAMEWORK DEFINITIONS
# ============================================================================

class Agency(Enum):
    POLICE = "police"
    LOCAL_AUTHORITY = "local_authority"
    CAFCASS = "cafcass"
    SOCIAL_WORKER = "social_worker"
    FAMILY_COURT = "family_court"
    MEDIA = "media"
    APPEAL_COURT = "appeal_court"

class BreachSeverity(Enum):
    CRITICAL = "critical"
    SERIOUS = "serious"
    MODERATE = "moderate"
    MINOR = "minor"

@dataclass
class StatutoryDuty:
    id: str
    agency: Agency
    title: str
    legal_basis: str
    description: str
    requirements: List[str]
    breach_indicators: List[str]
    breach_severity: BreachSeverity
    complaint_route: str
    relevant_case_law: List[str] = field(default_factory=list)

# Define all statutory duties
STATUTORY_DUTIES = [
    # POLICE
    StatutoryDuty(
        id="POLICE_001", agency=Agency.POLICE,
        title="Duty to Investigate Without Prejudice",
        legal_basis="PACE 1984; College of Policing APP",
        description="Police must conduct investigations objectively",
        requirements=["Gather all relevant evidence", "Document exculpatory evidence", "Interview suspects fairly"],
        breach_indicators=[
            "failure to investigate", "ignored evidence", "selective investigation",
            "predetermined outcome", "refused to consider", "wouldn't look at"
        ],
        breach_severity=BreachSeverity.CRITICAL,
        complaint_route="IOPC or Police Professional Standards"
    ),
    StatutoryDuty(
        id="POLICE_002", agency=Agency.POLICE,
        title="Disclosure Duty",
        legal_basis="CPIA 1996",
        description="Must disclose all material undermining prosecution or assisting defence",
        requirements=["Schedule all unused material", "Identify disclosable material", "Continuing duty"],
        breach_indicators=[
            "not disclosed", "late disclosure", "withheld", "failed to provide",
            "didn't receive", "wasn't given"
        ],
        breach_severity=BreachSeverity.CRITICAL,
        complaint_route="IOPC; s.78 PACE application"
    ),
    StatutoryDuty(
        id="POLICE_003", agency=Agency.POLICE,
        title="PACE Code C Compliance",
        legal_basis="PACE 1984 Code C",
        description="Fair treatment during detention and interview",
        requirements=["Right to legal representation", "Accurate recording", "Proper caution"],
        breach_indicators=[
            "no solicitor", "without legal advice", "oppressive", "interview records",
            "not cautioned properly"
        ],
        breach_severity=BreachSeverity.CRITICAL,
        complaint_route="IOPC; evidence exclusion application"
    ),
    
    # LOCAL AUTHORITY
    StatutoryDuty(
        id="LA_001", agency=Agency.LOCAL_AUTHORITY,
        title="Section 31 Threshold",
        legal_basis="Children Act 1989 s.31(2)",
        description="Care order only if threshold criteria met",
        requirements=["Significant harm", "Attributable to care given", "Balance of probabilities"],
        breach_indicators=[
            "no evidence of harm", "threshold not met", "not significant",
            "not attributable", "speculation", "no proof"
        ],
        breach_severity=BreachSeverity.CRITICAL,
        complaint_route="Challenge in proceedings; judicial review"
    ),
    StatutoryDuty(
        id="LA_002", agency=Agency.LOCAL_AUTHORITY,
        title="Duty of Candour",
        legal_basis="Working Together 2023; Re W (Children)",
        description="Must present all relevant information including that which undermines case",
        requirements=["Disclose all relevant documents", "Balanced assessments", "Update court on changes"],
        breach_indicators=[
            "didn't disclose", "withheld", "misleading", "failed to inform",
            "one-sided", "biased", "didn't mention"
        ],
        breach_severity=BreachSeverity.CRITICAL,
        complaint_route="Raise in proceedings; LGSCO"
    ),
    StatutoryDuty(
        id="LA_003", agency=Agency.LOCAL_AUTHORITY,
        title="Article 8 Proportionality",
        legal_basis="Human Rights Act 1998; ECHR Article 8",
        description="Interference with family life must be proportionate",
        requirements=["Necessary", "Proportionate", "Less intrusive measures considered"],
        breach_indicators=[
            "disproportionate", "unnecessary", "didn't consider alternatives",
            "excessive", "not necessary", "could have"
        ],
        breach_severity=BreachSeverity.CRITICAL,
        complaint_route="Raise in proceedings; HRA claim"
    ),
    StatutoryDuty(
        id="LA_004", agency=Agency.LOCAL_AUTHORITY,
        title="PLO Pre-Proceedings",
        legal_basis="Public Law Outline 2014; PD12A",
        description="Must follow pre-proceedings protocol before issuing",
        requirements=["Letter Before Proceedings", "Offer legal advice", "Family Group Conference"],
        breach_indicators=[
            "no letter before", "no pre-proceedings", "without warning",
            "emergency when not emergency", "no family meeting"
        ],
        breach_severity=BreachSeverity.SERIOUS,
        complaint_route="Challenge timetable in proceedings"
    ),
    
    # CAFCASS
    StatutoryDuty(
        id="CAFCASS_001", agency=Agency.CAFCASS,
        title="Independence and Impartiality",
        legal_basis="CJCS Act 2000 s.12; CAFCASS Operating Framework",
        description="Must act independently, representing child's interests",
        requirements=["Independent of all parties", "No predetermined conclusions", "Balanced analysis"],
        breach_indicators=[
            "adopted local authority position", "agreed with social worker",
            "didn't question", "accepted uncritically", "one-sided", "biased"
        ],
        breach_severity=BreachSeverity.CRITICAL,
        complaint_route="CAFCASS complaints; Parliamentary Ombudsman"
    ),
    StatutoryDuty(
        id="CAFCASS_002", agency=Agency.CAFCASS,
        title="Section 7 Report Requirements",
        legal_basis="Children Act 1989 s.7",
        description="Welfare report must meet procedural requirements",
        requirements=["Interview child", "Interview both parents", "Clear reasoned recommendations"],
        breach_indicators=[
            "didn't see child", "didn't speak to", "only interviewed one parent",
            "no recommendation", "didn't meet"
        ],
        breach_severity=BreachSeverity.SERIOUS,
        complaint_route="CAFCASS complaints; raise with court"
    ),
    StatutoryDuty(
        id="CAFCASS_003", agency=Agency.CAFCASS,
        title="Ascertain Child's Wishes",
        legal_basis="Children Act 1989 s.1(3)(a); UNCRC Article 12",
        description="Must ascertain and convey child's wishes to court",
        requirements=["See child alone", "Record views accurately", "Distinguish wishes from recommendation"],
        breach_indicators=[
            "child's wishes ignored", "didn't ask child", "child not seen",
            "didn't represent child's views"
        ],
        breach_severity=BreachSeverity.SERIOUS,
        complaint_route="CAFCASS complaints; challenge report"
    ),
    
    # SOCIAL WORKER
    StatutoryDuty(
        id="SW_001", agency=Agency.SOCIAL_WORKER,
        title="HCPC Standards",
        legal_basis="HCPC Standards of Proficiency",
        description="Must maintain professional standards",
        requirements=["Practice safely", "Within legal boundaries", "Effective communication"],
        breach_indicators=[
            "outside competence", "failed to follow", "poor record keeping",
            "inadequate communication", "unprofessional"
        ],
        breach_severity=BreachSeverity.SERIOUS,
        complaint_route="HCPC Fitness to Practise"
    ),
    StatutoryDuty(
        id="SW_002", agency=Agency.SOCIAL_WORKER,
        title="Accurate Recording",
        legal_basis="Working Together 2023; HCPC Standards",
        description="Must maintain accurate records",
        requirements=["Contemporaneous", "Distinguish fact from opinion", "Accurate attribution"],
        breach_indicators=[
            "inaccurate", "not what I said", "misquoted", "misrepresented",
            "wrong", "didn't record", "made up"
        ],
        breach_severity=BreachSeverity.SERIOUS,
        complaint_route="Employer; HCPC"
    ),
    StatutoryDuty(
        id="SW_003", agency=Agency.SOCIAL_WORKER,
        title="Anti-Oppressive Practice",
        legal_basis="BASW Code of Ethics; Equality Act 2010",
        description="Must practice without discrimination",
        requirements=["Recognise power imbalances", "Challenge discrimination", "Cultural competence"],
        breach_indicators=[
            "discriminatory", "stereotyping", "biased against", "prejudice",
            "assumption"
        ],
        breach_severity=BreachSeverity.SERIOUS,
        complaint_route="HCPC; Equality and Human Rights Commission"
    ),
    
    # FAMILY COURT
    StatutoryDuty(
        id="COURT_001", agency=Agency.FAMILY_COURT,
        title="Article 6 Fair Trial",
        legal_basis="Human Rights Act 1998; ECHR Article 6",
        description="Every party entitled to fair hearing",
        requirements=["Reasonable time", "Access to evidence", "Opportunity to present case", "Reasoned judgment"],
        breach_indicators=[
            "wasn't heard", "didn't allow", "refused to consider",
            "no opportunity", "cut off", "not enough time"
        ],
        breach_severity=BreachSeverity.CRITICAL,
        complaint_route="Appeal; JCIO"
    ),
    StatutoryDuty(
        id="COURT_002", agency=Agency.FAMILY_COURT,
        title="Welfare Checklist",
        legal_basis="Children Act 1989 s.1(3)",
        description="Must consider all welfare checklist factors",
        requirements=["Child's wishes", "Needs", "Effect of change", "Harm", "Capability of parents"],
        breach_indicators=[
            "didn't consider", "ignored", "no analysis", "failed to address",
            "overlooked"
        ],
        breach_severity=BreachSeverity.SERIOUS,
        complaint_route="Appeal"
    ),
    StatutoryDuty(
        id="COURT_003", agency=Agency.FAMILY_COURT,
        title="Reasons for Judgment",
        legal_basis="FPR 2010; Re G [2014]",
        description="Must give adequate reasons for decisions",
        requirements=["Clear reasoning", "Address key issues", "Explain weight given to evidence"],
        breach_indicators=[
            "no reasons", "didn't explain", "no rationale", "unclear why",
            "unexplained"
        ],
        breach_severity=BreachSeverity.SERIOUS,
        complaint_route="Appeal"
    ),
    
    # MEDIA
    StatutoryDuty(
        id="MEDIA_001", agency=Agency.MEDIA,
        title="Section 97 Publication Restrictions",
        legal_basis="Children Act 1989 s.97",
        description="Criminal offence to identify child in family proceedings",
        requirements=["Not identify child", "Court permission for publication"],
        breach_indicators=[
            "identified", "named", "recognisable", "published", "filmed",
            "broadcast", "documentary"
        ],
        breach_severity=BreachSeverity.CRITICAL,
        complaint_route="Ofcom; contempt of court; police"
    ),
    StatutoryDuty(
        id="MEDIA_002", agency=Agency.MEDIA,
        title="Ofcom Broadcasting Code",
        legal_basis="Communications Act 2003; Ofcom Code",
        description="Must comply with fairness and privacy standards",
        requirements=["Informed consent", "Fair treatment", "Privacy protections", "Accuracy"],
        breach_indicators=[
            "no consent", "unfair", "privacy", "inaccurate", "misleading",
            "one-sided", "didn't agree"
        ],
        breach_severity=BreachSeverity.SERIOUS,
        complaint_route="Ofcom complaint; legal action"
    ),
    
    # APPEAL COURT
    StatutoryDuty(
        id="APPEAL_001", agency=Agency.APPEAL_COURT,
        title="Permission Criteria",
        legal_basis="CPR 52.6; FPR 30.3",
        description="Must properly consider permission to appeal",
        requirements=["Real prospect of success", "Compelling reason", "Reasons for refusal"],
        breach_indicators=[
            "refused without reasons", "didn't consider", "no proper consideration",
            "inadequate reasons"
        ],
        breach_severity=BreachSeverity.SERIOUS,
        complaint_route="Renewed application; JCIO"
    ),
]

# Agency keywords for content filtering
AGENCY_KEYWORDS = {
    Agency.POLICE: [
        r'\bpolice\b', r'\bconstabulary\b', r'\bdetective\b', r'\bdc\b', r'\bdci\b',
        r'\barrest\b', r'\bbail\b', r'\binvestigation\b', r'\boperation scan\b',
        r'\bmurder\b', r'\bconspiracy\b', r'\bpace\b', r'\bcaution\b', r'\batkinson\b',
        r'\bdounias\b'
    ],
    Agency.LOCAL_AUTHORITY: [
        r'\blocal authority\b', r'\bcouncil\b', r'\bcambridgeshire\b', r'\bla\b',
        r'\bcare proceedings\b', r'\bsection 31\b', r'\bsection 47\b', r'\bico\b',
        r'\binterim care\b', r'\bcare plan\b', r'\bthreshold\b', r'\bccc\b'
    ],
    Agency.CAFCASS: [
        r'\bcafcass\b', r'\bguardian\b', r'\bsection 7\b', r'\brule 16\b',
        r'\bchildren.s guardian\b', r'\bfamily court adviser\b'
    ],
    Agency.SOCIAL_WORKER: [
        r'\bsocial worker\b', r'\bsw\b', r'\bassessment\b', r'\bvisit\b',
        r'\bchild protection\b', r'\bsafeguarding\b', r'\bcase conference\b',
        r'\bbutler\b'  # Social worker name from documents
    ],
    Agency.FAMILY_COURT: [
        r'\bjudge\b', r'\bhearing\b', r'\bcourt\b', r'\border\b', r'\bjudgment\b',
        r'\bhhj\b', r'\brecorder\b', r'\bdjm\b', r'\bdistrict judge\b',
        r'\bgordon-saker\b'
    ],
    Agency.MEDIA: [
        r'\bchannel 4\b', r'\b24 hours\b', r'\bcustody\b', r'\bfilming\b',
        r'\bdocumentary\b', r'\bmedia\b', r'\bbroadcast\b', r'\bpress\b'
    ],
    Agency.APPEAL_COURT: [
        r'\bappeal\b', r'\bcourt of appeal\b', r'\bpermission\b', r'\bca-\b',
        r'\bcivil division\b'
    ]
}

# ============================================================================
# AUDIT ENGINE
# ============================================================================

def run_audit():
    """Run the full accountability audit."""
    db_path = 'Phronesis/data/db/phronesis.db'
    
    print("="*70)
    print("ACCOUNTABILITY AUDIT - MULTI-AGENCY INVESTIGATION")
    print("Case: PE23C50095 - JFD vs SJS Family Proceedings")
    print("="*70)
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Load all claims
    cursor.execute("""
        SELECT c.*, d.filename, d.title as doc_title, d.document_category
        FROM claims c
        LEFT JOIN documents d ON c.document_id = d.id
    """)
    claims = [dict(row) for row in cursor.fetchall()]
    print(f"\nLoaded {len(claims)} claims for analysis")
    
    # Run audit for each agency
    results = {}
    total_breaches = 0
    
    for agency in Agency:
        print(f"\n{'='*50}")
        print(f"AUDITING: {agency.value.upper()}")
        print('='*50)
        
        # Get duties for this agency
        duties = [d for d in STATUTORY_DUTIES if d.agency == agency]
        
        # Get relevant keywords
        keywords = AGENCY_KEYWORDS.get(agency, [])
        pattern = '|'.join(keywords) if keywords else None
        
        # Filter claims
        if pattern:
            relevant_claims = [
                c for c in claims 
                if re.search(pattern, (c.get('claim_text', '') + ' ' + (c.get('context') or '')).lower())
            ]
        else:
            relevant_claims = claims
        
        print(f"  Relevant claims: {len(relevant_claims)}")
        
        # Check each duty
        agency_breaches = []
        
        for duty in duties:
            for indicator in duty.breach_indicators:
                # Create search pattern
                indicator_words = indicator.lower().split()
                search_pattern = r'|'.join([re.escape(w) for w in indicator_words])
                
                # Find matching claims
                matches = []
                for claim in relevant_claims:
                    text = (claim.get('claim_text', '') or '').lower()
                    if re.search(search_pattern, text):
                        matches.append({
                            'claim_text': claim.get('claim_text', ''),
                            'author': claim.get('asserted_by'),
                            'date': claim.get('date_made'),
                            'document': claim.get('filename') or claim.get('doc_title')
                        })
                
                if matches:
                    agency_breaches.append({
                        'duty_id': duty.id,
                        'duty_title': duty.title,
                        'legal_basis': duty.legal_basis,
                        'indicator': indicator,
                        'severity': duty.breach_severity.value,
                        'complaint_route': duty.complaint_route,
                        'evidence_count': len(matches),
                        'evidence': matches[:5]  # First 5 examples
                    })
        
        results[agency.value] = {
            'total_breaches': len(agency_breaches),
            'critical': sum(1 for b in agency_breaches if b['severity'] == 'critical'),
            'serious': sum(1 for b in agency_breaches if b['severity'] == 'serious'),
            'breaches': agency_breaches
        }
        
        total_breaches += len(agency_breaches)
        
        # Print summary for this agency
        if agency_breaches:
            print(f"\n  ⚠️  {len(agency_breaches)} POTENTIAL BREACHES IDENTIFIED")
            critical = results[agency.value]['critical']
            serious = results[agency.value]['serious']
            print(f"     CRITICAL: {critical} | SERIOUS: {serious}")
            
            # Show top breaches
            for breach in agency_breaches[:3]:
                print(f"\n  [{breach['severity'].upper()}] {breach['duty_title']}")
                print(f"     Legal basis: {breach['legal_basis']}")
                print(f"     Indicator: {breach['indicator']}")
                print(f"     Evidence: {breach['evidence_count']} instances")
                print(f"     Complaint route: {breach['complaint_route']}")
        else:
            print(f"  ✓ No clear breaches identified")
    
    # Generate summary report
    print("\n" + "="*70)
    print("ACCOUNTABILITY AUDIT SUMMARY")
    print("="*70)
    print(f"\nTotal Potential Breaches: {total_breaches}")
    
    print("\nBy Agency:")
    for agency_name, data in results.items():
        if data['total_breaches'] > 0:
            print(f"  {agency_name.upper():20} : {data['total_breaches']:3} breaches ({data['critical']} critical, {data['serious']} serious)")
    
    # Critical findings
    print("\n" + "-"*70)
    print("CRITICAL FINDINGS REQUIRING IMMEDIATE ACTION")
    print("-"*70)
    
    critical_count = 0
    for agency_name, data in results.items():
        for breach in data['breaches']:
            if breach['severity'] == 'critical':
                critical_count += 1
                print(f"\n{critical_count}. [{agency_name.upper()}] {breach['duty_title']}")
                print(f"   Legal basis: {breach['legal_basis']}")
                print(f"   Breach indicator: {breach['indicator']}")
                print(f"   Complaint route: {breach['complaint_route']}")
                print(f"   Evidence instances: {breach['evidence_count']}")
                if breach['evidence']:
                    print(f"   Example: \"{breach['evidence'][0]['claim_text'][:100]}...\"")
    
    # Recommended actions
    print("\n" + "-"*70)
    print("RECOMMENDED ACTIONS")
    print("-"*70)
    
    recommendations = []
    
    if results.get('police', {}).get('critical', 0) > 0:
        recommendations.append("1. IOPC Complaint - Police failures in investigation/disclosure")
    
    if results.get('local_authority', {}).get('critical', 0) > 0:
        recommendations.append("2. LGSCO Complaint - Local Authority failures (candour, proportionality)")
    
    if results.get('cafcass', {}).get('critical', 0) > 0:
        recommendations.append("3. CAFCASS Complaint - Independence/impartiality failures")
    
    if results.get('social_worker', {}).get('serious', 0) > 0:
        recommendations.append("4. HCPC Referral - Social worker professional standards")
    
    if results.get('family_court', {}).get('critical', 0) > 0:
        recommendations.append("5. Appeal/Judicial Review - Procedural unfairness")
    
    if results.get('media', {}).get('total_breaches', 0) > 0:
        recommendations.append("6. Ofcom Complaint - Channel 4 Broadcasting Code violations")
    
    total_critical = sum(d.get('critical', 0) for d in results.values())
    if total_critical >= 3:
        recommendations.append("7. CONSIDER: Human Rights Act claim - multiple Article 6/8 violations")
    if total_critical >= 5:
        recommendations.append("8. CONSIDER: Parliamentary Ombudsman - systemic maladministration")
    
    for rec in recommendations:
        print(f"  {rec}")
    
    # Save full report
    report = {
        'case_reference': 'PE23C50095',
        'generated_at': datetime.now().isoformat(),
        'total_breaches': total_breaches,
        'agency_results': results,
        'recommendations': recommendations
    }
    
    os.makedirs('data', exist_ok=True)
    with open('data/accountability_audit_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n\nFull report saved to: data/accountability_audit_report.json")
    
    conn.close()
    return report

if __name__ == "__main__":
    run_audit()

