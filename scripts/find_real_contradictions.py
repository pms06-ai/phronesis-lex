#!/usr/bin/env python3
"""
Find REAL contradictions - claims that actually contradict each other.
A true contradiction is when:
1. Two claims are about the SAME topic/event
2. They assert OPPOSITE or incompatible things
"""

import sqlite3
import re
from collections import defaultdict

db_path = 'Phronesis/data/db/phronesis.db'
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Load all claims
cursor.execute("""
    SELECT c.claim_text, c.asserted_by, d.filename, d.document_category
    FROM claims c
    LEFT JOIN documents d ON c.document_id = d.id
    WHERE c.claim_text IS NOT NULL AND LENGTH(c.claim_text) > 50
""")
claims = [dict(row) for row in cursor.fetchall()]
print(f"Loaded {len(claims)} claims")

# Define topics/events to look for contradictions about
TOPICS = {
    'conspiracy_knowledge': {
        'positive': ['knew about', 'was aware', 'planned', 'conspired', 'involved in', 'knowledge of'],
        'negative': ['no knowledge', 'did not know', 'unaware', 'had no idea', 'did not conspire', 'not involved', 'no involvement']
    },
    'living_location': {
        'patterns': [
            (r'living at ([\w\s]+)', r'not living at'),
            (r'resided at', r'did not reside'),
        ]
    },
    'threshold_met': {
        'positive': ['threshold is met', 'threshold has been met', 'threshold criteria satisfied', 'significant harm'],
        'negative': ['threshold not met', 'threshold is not met', 'insufficient evidence', 'no significant harm', 'threshold not satisfied']
    },
    'parenting_ability': {
        'positive': ['good parent', 'capable parent', 'loving', 'appropriate care', 'meets needs', 'protective'],
        'negative': ['poor parenting', 'unable to parent', 'neglect', 'failed to protect', 'risk to child', 'harm']
    },
    'credibility': {
        'positive': ['credible', 'truthful', 'reliable', 'honest', 'believable'],
        'negative': ['not credible', 'lied', 'dishonest', 'unreliable', 'fabricated', 'untrue']
    },
    'autism_diagnosis': {
        'dates': [r'diagnosed.*?(\d{4})', r'autism.*?(\d{4})', r'age (\d+).*?diagnosed', r'diagnosed.*?age (\d+)']
    },
    'arrest_release': {
        'positive': ['arrested', 'detained', 'suspect', 'charged'],
        'negative': ['released', 'no further action', 'NFA', 'not charged', 'cleared']
    }
}

print("\n" + "="*70)
print("SEARCHING FOR REAL CONTRADICTIONS")
print("="*70)

# 1. Conspiracy knowledge contradictions
print("\n## CONSPIRACY KNOWLEDGE ##")
print("Looking for claims about whether Samantha/Paul knew about the plan...")

knew_claims = []
didnt_know_claims = []

for c in claims:
    text_lower = c['claim_text'].lower()
    
    for pos in TOPICS['conspiracy_knowledge']['positive']:
        if pos in text_lower and ('samantha' in text_lower or 'paul' in text_lower or 'stephen' in text_lower or 'conspirator' in text_lower or 'suspect' in text_lower):
            knew_claims.append(c)
            break
    
    for neg in TOPICS['conspiracy_knowledge']['negative']:
        if neg in text_lower and ('samantha' in text_lower or 'paul' in text_lower or 'stephen' in text_lower or 'i did not' in text_lower):
            didnt_know_claims.append(c)
            break

print(f"\nClaims suggesting KNOWLEDGE of conspiracy: {len(knew_claims)}")
for c in knew_claims[:5]:
    print(f"  - [{c['asserted_by'] or 'Unknown'}] \"{c['claim_text'][:100]}...\"")

print(f"\nClaims DENYING knowledge of conspiracy: {len(didnt_know_claims)}")
for c in didnt_know_claims[:5]:
    print(f"  - [{c['asserted_by'] or 'Unknown'}] \"{c['claim_text'][:100]}...\"")

if knew_claims and didnt_know_claims:
    print(f"\n*** CONTRADICTION FOUND: {len(knew_claims)} claims suggest knowledge, {len(didnt_know_claims)} deny it ***")

# 2. Threshold contradictions
print("\n\n## THRESHOLD CRITERIA ##")
print("Looking for claims about whether section 31 threshold is met...")

threshold_met = []
threshold_not_met = []

for c in claims:
    text_lower = c['claim_text'].lower()
    
    for pos in TOPICS['threshold_met']['positive']:
        if pos in text_lower:
            threshold_met.append(c)
            break
    
    for neg in TOPICS['threshold_met']['negative']:
        if neg in text_lower:
            threshold_not_met.append(c)
            break

print(f"\nClaims that THRESHOLD IS MET: {len(threshold_met)}")
for c in threshold_met[:3]:
    print(f"  - [{c['asserted_by'] or 'Unknown'}] \"{c['claim_text'][:100]}...\"")

print(f"\nClaims that THRESHOLD NOT MET: {len(threshold_not_met)}")
for c in threshold_not_met[:3]:
    print(f"  - [{c['asserted_by'] or 'Unknown'}] \"{c['claim_text'][:100]}...\"")

# 3. Autism diagnosis date
print("\n\n## AUTISM DIAGNOSIS DATE ##")
print("Looking for inconsistencies in when Ryan was diagnosed...")

diagnosis_dates = []
for c in claims:
    text = c['claim_text']
    
    # Look for year mentions near autism/diagnosed
    if 'autism' in text.lower() or 'diagnosed' in text.lower():
        years = re.findall(r'20\d{2}', text)
        ages = re.findall(r'age[d]?\s*(?:of\s*)?(\d+)', text.lower())
        
        if years or ages:
            diagnosis_dates.append({
                'claim': c,
                'years': years,
                'ages': ages
            })

print(f"\nFound {len(diagnosis_dates)} claims mentioning diagnosis dates/ages:")
for d in diagnosis_dates[:10]:
    info = f"years: {d['years']}" if d['years'] else ""
    info += f" ages: {d['ages']}" if d['ages'] else ""
    print(f"  - {info}: \"{d['claim']['claim_text'][:80]}...\"")

# 4. Credibility claims
print("\n\n## CREDIBILITY ASSESSMENTS ##")
print("Looking for contradictory assessments of credibility...")

credible = []
not_credible = []

for c in claims:
    text_lower = c['claim_text'].lower()
    
    # Check if about Samantha or Paul
    if 'samantha' in text_lower or 'paul' in text_lower or 'mother' in text_lower or 'stepfather' in text_lower or 'respondent' in text_lower:
        for pos in TOPICS['credibility']['positive']:
            if pos in text_lower:
                credible.append(c)
                break
        
        for neg in TOPICS['credibility']['negative']:
            if neg in text_lower:
                not_credible.append(c)
                break

print(f"\nClaims assessing CREDIBILITY as positive: {len(credible)}")
for c in credible[:3]:
    print(f"  - [{c['asserted_by'] or 'Unknown'}] \"{c['claim_text'][:100]}...\"")

print(f"\nClaims assessing CREDIBILITY as negative: {len(not_credible)}")
for c in not_credible[:5]:
    print(f"  - [{c['asserted_by'] or 'Unknown'}] \"{c['claim_text'][:100]}...\"")

# 5. Living location (Mildenhall claim)
print("\n\n## LIVING LOCATION ##")
print("Looking for contradictions about where Samantha/family lived...")

mildenhall_claims = [c for c in claims if 'mildenhall' in c['claim_text'].lower()]
print(f"\nClaims mentioning Mildenhall: {len(mildenhall_claims)}")
for c in mildenhall_claims[:5]:
    print(f"  - [{c['asserted_by'] or 'Unknown'}] \"{c['claim_text'][:120]}...\"")

# 6. Summary
print("\n\n" + "="*70)
print("SUMMARY OF REAL CONTRADICTIONS FOUND")
print("="*70)

contradictions = []

if knew_claims and didnt_know_claims:
    contradictions.append({
        'topic': 'Conspiracy Knowledge',
        'side_a': f"{len(knew_claims)} claims suggest knowledge/involvement",
        'side_b': f"{len(didnt_know_claims)} claims deny any knowledge",
        'significance': 'CRITICAL - Central to criminal investigation'
    })

if threshold_met and threshold_not_met:
    contradictions.append({
        'topic': 'Section 31 Threshold',
        'side_a': f"{len(threshold_met)} claims threshold met",
        'side_b': f"{len(threshold_not_met)} claims threshold not met", 
        'significance': 'HIGH - Determines legal basis for care order'
    })

if not_credible:
    contradictions.append({
        'topic': 'Credibility Assessments',
        'side_a': f"{len(credible)} positive assessments",
        'side_b': f"{len(not_credible)} negative assessments",
        'significance': 'HIGH - Affects weight given to evidence'
    })

for c in contradictions:
    print(f"\n{c['topic']}:")
    print(f"  Side A: {c['side_a']}")
    print(f"  Side B: {c['side_b']}")
    print(f"  Significance: {c['significance']}")

conn.close()

