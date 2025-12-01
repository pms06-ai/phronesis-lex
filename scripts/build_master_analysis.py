"""
Master Analysis Script - Comprehensive case analysis combining all engines.

This generates:
1. Cross-reference of murder investigation vs family court timeline
2. Professional accountability tracking
3. Contradiction analysis
4. Bias detection
5. Evidence mapping
6. Actionable findings report
"""

import sqlite3
import json
import re
import os
from datetime import datetime
from collections import defaultdict
from typing import List, Dict, Tuple

# ============================================================================
# DATABASE CONNECTION
# ============================================================================

conn = sqlite3.connect('Phronesis/data/db/phronesis.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

os.makedirs('data/analysis', exist_ok=True)

print("="*80)
print("MASTER CASE ANALYSIS - PE23C50095")
print("JFD vs SJS Family Proceedings (2021-2025)")
print("="*80)

# ============================================================================
# 1. LOAD ALL DATA
# ============================================================================

print("\n[1/6] Loading case data...")

# Claims
cursor.execute("""
    SELECT c.*, d.filename, d.title, d.document_category, d.document_date
    FROM claims c
    LEFT JOIN documents d ON c.document_id = d.id
""")
claims = [dict(row) for row in cursor.fetchall()]
print(f"  Claims: {len(claims)}")

# Documents
cursor.execute("SELECT * FROM documents")
documents = [dict(row) for row in cursor.fetchall()]
print(f"  Documents: {len(documents)}")

# Entities
cursor.execute("SELECT * FROM entities")
entities = [dict(row) for row in cursor.fetchall()]
print(f"  Entities: {len(entities)}")

# Cases
cursor.execute("SELECT * FROM cases")
cases = [dict(row) for row in cursor.fetchall()]
print(f"  Cases: {len(cases)}")

# ============================================================================
# 2. MURDER INVESTIGATION CROSS-REFERENCE
# ============================================================================

print("\n[2/6] Building murder investigation cross-reference...")

# Key murder investigation events
murder_timeline = [
    {'date': '2022-04', 'event': 'Stephen Alderton texts "Panama"', 'type': 'PREMEDITATION'},
    {'date': '2022-06', 'event': 'Alderton texts "Plan B", "Independence Day"', 'type': 'PREMEDITATION'},
    {'date': '2023-03-27', 'event': 'Family Court - CAFCASS: Child NOT to leave UK', 'type': 'COURT'},
    {'date': '2023-03-29', 'event': 'MURDERS: Joshua & Gary Dunmore killed', 'type': 'CRIME'},
    {'date': '2023-03-30', 'event': 'Paul & Samantha arrested (conspiracy)', 'type': 'ARREST'},
    {'date': '2023-03-31', 'event': 'Released NFA', 'type': 'POLICE'},
    {'date': '2023-05-12', 'event': 'Suspect status reinstated', 'type': 'POLICE'},
    {'date': '2023-06-07', 'event': 'Re-arrested, "no comment" interviews', 'type': 'ARREST'},
    {'date': '2025-02-12', 'event': 'Final NFA - insufficient evidence', 'type': 'POLICE'},
]

# Family court events
family_court_timeline = [
    {'date': '2021', 'event': 'PE21P30644 - Original private law proceedings', 'type': 'PROCEEDINGS'},
    {'date': '2022-05', 'event': 'PE22P00090 - Cambridge proceedings', 'type': 'PROCEEDINGS'},
    {'date': '2022', 'event': 'PE22P31058 - Peterborough proceedings', 'type': 'PROCEEDINGS'},
    {'date': '2023-04', 'event': 'PE23C50063 - Initial care application', 'type': 'CARE'},
    {'date': '2023-06-09', 'event': 'PE23C50095 - Urgent ICO hearing', 'type': 'CARE'},
    {'date': '2023', 'event': 'PE23P30344 - New private law (Seamark)', 'type': 'PROCEEDINGS'},
    {'date': '2024', 'event': 'CA-2024-001096 - Appeal refused', 'type': 'APPEAL'},
]

# Merge timelines
combined_timeline = []
for event in murder_timeline:
    event['source'] = 'MURDER_INVESTIGATION'
    combined_timeline.append(event)
for event in family_court_timeline:
    event['source'] = 'FAMILY_COURT'
    combined_timeline.append(event)

combined_timeline.sort(key=lambda x: x['date'])

# Save cross-reference
with open('data/analysis/cross_reference_timeline.json', 'w') as f:
    json.dump(combined_timeline, f, indent=2)

print(f"  Combined timeline: {len(combined_timeline)} events")

# ============================================================================
# 3. DOCUMENT-BASED PROFESSIONAL ANALYSIS
# ============================================================================

print("\n[3/6] Analyzing professionals by document authorship...")

# Extract authors from documents
doc_authors = defaultdict(list)
for doc in documents:
    # Extract from filename patterns
    filename = doc.get('filename') or ''
    title = doc.get('title') or ''
    author = ''  # No document_author column
    
    # Common patterns
    patterns = [
        (r'butler', 'Butler (Social Worker)'),
        (r'duggan', 'Paul Duggan (Social Worker)'),
        (r'ardern', 'Lucy Ardern (Social Worker)'),
        (r'cafcass', 'CAFCASS'),
        (r'guardian', 'Guardian'),
        (r'section.?7', 'CAFCASS'),
        (r'police', 'Police'),
        (r'dounias', 'DCI Dounias'),
        (r'atkinson', 'DC Atkinson'),
        (r'seamark', 'Mandy Seamark'),
        (r'stephen', 'Stephen Family'),
    ]
    
    combined = (filename + ' ' + author).lower()
    for pattern, name in patterns:
        if re.search(pattern, combined):
            doc_authors[name].append(doc)

# Analyze each professional
professional_profiles = {}
for name, docs in doc_authors.items():
    profile = {
        'name': name,
        'document_count': len(docs),
        'document_types': list(set(d.get('document_category') for d in docs if d.get('document_category'))),
        'documents': [d.get('filename') or d.get('title') for d in docs][:10]
    }
    professional_profiles[name] = profile

print(f"  Professionals identified: {len(professional_profiles)}")

# ============================================================================
# 4. CLAIM ANALYSIS BY DOCUMENT TYPE
# ============================================================================

print("\n[4/6] Analyzing claims by document type and source...")

claims_by_type = defaultdict(list)
claims_by_source = defaultdict(list)

# Keywords for key topics
topic_keywords = {
    'MURDER': ['murder', 'kill', 'alderton', 'dunmore', 'joshua', 'gary', 'shot', 'conspiracy'],
    'CUSTODY': ['custody', 'care', 'placement', 'foster', 'child arrangement'],
    'THRESHOLD': ['threshold', 'significant harm', 'section 31', 'likely to suffer'],
    'CONTACT': ['contact', 'visit', 'family time', 'supervised'],
    'CAFCASS': ['cafcass', 'guardian', 'section 7', 'welfare'],
    'POLICE': ['police', 'arrest', 'bail', 'investigation', 'interview'],
    'CREDIBILITY': ['credibility', 'lie', 'dishonest', 'false', 'misleading'],
}

claims_by_topic = defaultdict(list)

for claim in claims:
    doc_type = claim.get('document_category') or 'unknown'
    claims_by_type[doc_type].append(claim)
    
    # Categorize by topic
    text = (claim.get('claim_text') or '').lower()
    for topic, keywords in topic_keywords.items():
        if any(kw in text for kw in keywords):
            claims_by_topic[topic].append(claim)

print("  Claims by document type:")
for doc_type, type_claims in sorted(claims_by_type.items(), key=lambda x: -len(x[1]))[:10]:
    print(f"    {doc_type}: {len(type_claims)}")

print("  Claims by topic:")
for topic, topic_claims in sorted(claims_by_topic.items(), key=lambda x: -len(x[1])):
    print(f"    {topic}: {len(topic_claims)}")

# ============================================================================
# 5. CRITICAL FINDINGS EXTRACTION
# ============================================================================

print("\n[5/6] Extracting critical findings...")

critical_findings = []

# Find claims about key events
key_searches = [
    ('MOTIVE', 'motive', 'What was the alleged motive?'),
    ('PREMEDITATION', 'plan|premeditat|independence day|panama', 'Evidence of premeditation'),
    ('POLICE_FAILURE', 'fail.*investigat|not disclosed|didn\'t provide', 'Police investigation failures'),
    ('LA_FAILURE', 'threshold not met|no evidence of harm|disproportionate', 'Local Authority failures'),
    ('CAFCASS_BIAS', 'adopted.*position|agreed with|one-sided', 'CAFCASS independence issues'),
    ('CREDIBILITY', 'lied|false|dishonest|not credible', 'Credibility findings'),
    ('COURT_PROCESS', 'wasn\'t heard|no opportunity|refused to consider', 'Procedural unfairness'),
]

for finding_type, pattern, description in key_searches:
    matching_claims = []
    for claim in claims:
        text = (claim.get('claim_text') or '').lower()
        if re.search(pattern, text):
            matching_claims.append({
                'text': claim.get('claim_text'),
                'document': claim.get('filename') or claim.get('title'),
                'date': claim.get('date_made') or claim.get('document_date'),
                'author': claim.get('asserted_by')
            })
    
    if matching_claims:
        critical_findings.append({
            'type': finding_type,
            'description': description,
            'count': len(matching_claims),
            'examples': matching_claims[:5]
        })

print(f"  Critical findings categories: {len(critical_findings)}")
for finding in critical_findings:
    print(f"    {finding['type']}: {finding['count']} instances")

# ============================================================================
# 6. GENERATE COMPREHENSIVE REPORT
# ============================================================================

print("\n[6/6] Generating comprehensive report...")

master_report = {
    'generated_at': datetime.now().isoformat(),
    'case_reference': 'PE23C50095',
    'case_title': 'JFD vs SJS Family Proceedings',
    
    'summary': {
        'total_documents': len(documents),
        'total_claims': len(claims),
        'total_entities': len(entities),
        'cases_tracked': len(cases),
        'professionals_identified': len(professional_profiles),
        'critical_finding_categories': len(critical_findings),
    },
    
    'cases': [
        {'reference': c.get('reference'), 'title': c.get('title'), 'status': c.get('status')}
        for c in cases
    ],
    
    'cross_reference_timeline': combined_timeline,
    
    'claims_by_topic': {
        topic: {
            'count': len(topic_claims),
            'examples': [c.get('claim_text')[:100] for c in topic_claims[:5]]
        }
        for topic, topic_claims in claims_by_topic.items()
    },
    
    'claims_by_document_type': {
        doc_type: len(type_claims)
        for doc_type, type_claims in claims_by_type.items()
    },
    
    'professionals': professional_profiles,
    
    'critical_findings': critical_findings,
    
    'key_dates': {
        'murder_date': '2023-03-29',
        'first_arrest': '2023-03-30',
        'care_proceedings_start': '2023-06-09',
        'appeal_refused': '2024',
        'final_nfa': '2025-02-12',
    },
    
    'accountability_targets': [
        {
            'agency': 'Police',
            'key_individuals': ['DCI Katie Dounias', 'DC 2072 Atkinson'],
            'complaint_route': 'IOPC',
            'issues': 'Investigation conduct, disclosure'
        },
        {
            'agency': 'Local Authority',
            'key_individuals': ['Social Workers (multiple)'],
            'complaint_route': 'LGSCO',
            'issues': 'Threshold, candour, proportionality'
        },
        {
            'agency': 'CAFCASS',
            'key_individuals': ['Guardian'],
            'complaint_route': 'CAFCASS Complaints',
            'issues': 'Independence, impartiality'
        },
        {
            'agency': 'Family Court',
            'key_individuals': ['HHJ Gordon-Saker'],
            'complaint_route': 'JCIO / Appeal',
            'issues': 'Procedural fairness'
        },
        {
            'agency': 'Channel 4',
            'key_individuals': ['Unknown'],
            'complaint_route': 'Ofcom',
            'issues': 's.97 identification, consent'
        },
    ]
}

# Save master report
with open('data/analysis/MASTER_REPORT.json', 'w', encoding='utf-8') as f:
    json.dump(master_report, f, indent=2, ensure_ascii=False, default=str)

# Generate readable summary
with open('data/analysis/EXECUTIVE_SUMMARY.txt', 'w', encoding='utf-8') as f:
    f.write("="*80 + "\n")
    f.write("EXECUTIVE SUMMARY - FORENSIC CASE INTELLIGENCE REPORT\n")
    f.write("="*80 + "\n")
    f.write(f"\nCase: PE23C50095 - JFD vs SJS Family Proceedings\n")
    f.write(f"Generated: {datetime.now().strftime('%d %B %Y %H:%M')}\n")
    
    f.write("\n" + "="*80 + "\n")
    f.write("CASE OVERVIEW\n")
    f.write("="*80 + "\n")
    f.write(f"""
This case involves family court proceedings following the murders of Joshua 
Dunmore (father) and Gary Dunmore (grandfather) on 29 March 2023. Stephen 
Alderton (maternal grandfather) was convicted and sentenced to life with 
30-year minimum tariff.

Paul and Samantha Stephen (parents) were investigated for conspiracy to 
murder for almost 2 years before receiving No Further Action on 12 Feb 2025.

Care proceedings were initiated for the children (Ryan and Freya) in the 
immediate aftermath of the murders.
""")
    
    f.write("\n" + "="*80 + "\n")
    f.write("KEY STATISTICS\n")
    f.write("="*80 + "\n")
    f.write(f"""
  Documents analyzed:        {len(documents):,}
  Claims extracted:          {len(claims):,}
  Entities tracked:          {len(entities)}
  Cases tracked:             {len(cases)}
  Professionals identified:  {len(professional_profiles)}
  Critical finding types:    {len(critical_findings)}
""")
    
    f.write("\n" + "="*80 + "\n")
    f.write("CRITICAL FINDINGS\n")
    f.write("="*80 + "\n")
    
    for finding in critical_findings:
        f.write(f"\n{finding['type']} ({finding['count']} instances)\n")
        f.write(f"  {finding['description']}\n")
        if finding['examples']:
            f.write(f"  Example: \"{finding['examples'][0]['text'][:100]}...\"\n")
    
    f.write("\n" + "="*80 + "\n")
    f.write("ACCOUNTABILITY TARGETS\n")
    f.write("="*80 + "\n")
    
    for target in master_report['accountability_targets']:
        f.write(f"\n{target['agency']}\n")
        f.write(f"  Key individuals: {', '.join(target['key_individuals'])}\n")
        f.write(f"  Issues: {target['issues']}\n")
        f.write(f"  Complaint route: {target['complaint_route']}\n")
    
    f.write("\n" + "="*80 + "\n")
    f.write("TIMELINE OF KEY EVENTS\n")
    f.write("="*80 + "\n")
    
    for event in combined_timeline:
        f.write(f"\n{event['date']:12} | {event['source']:18} | {event['event']}\n")
    
    f.write("\n" + "="*80 + "\n")
    f.write("RECOMMENDED ACTIONS\n")
    f.write("="*80 + "\n")
    f.write("""
1. IOPC COMPLAINT - Police investigation failures
2. LGSCO COMPLAINT - Local Authority maladministration
3. CAFCASS COMPLAINT - Independence failures
4. HCPC REFERRAL - Individual social worker conduct
5. APPEAL/JUDICIAL REVIEW - Procedural unfairness
6. OFCOM COMPLAINT - Channel 4 broadcasting (if applicable)
7. HUMAN RIGHTS CLAIM - Article 6/8 violations
8. PARLIAMENTARY OMBUDSMAN - Systemic failures
""")

print(f"\n{'='*80}")
print("ANALYSIS COMPLETE")
print("="*80)
print(f"""
Files generated in data/analysis/:
  - MASTER_REPORT.json        (Full machine-readable report)
  - EXECUTIVE_SUMMARY.txt     (Human-readable summary)
  - cross_reference_timeline.json (Murder vs Family Court timeline)

Summary:
  - {len(documents)} documents analyzed
  - {len(claims)} claims extracted
  - {len(critical_findings)} critical finding categories
  - {len(combined_timeline)} timeline events mapped
""")

conn.close()

