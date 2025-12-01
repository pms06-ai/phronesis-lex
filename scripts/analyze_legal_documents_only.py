#!/usr/bin/env python3
"""
Analyze ONLY official legal documents and emails.
Excludes: medical records, expert reports, school records, text messages, etc.
"""

import sqlite3
import json
import re
from collections import defaultdict
from datetime import datetime

db_path = 'Phronesis/data/db/phronesis.db'
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Define which document types to include
# Including expert_report for Dr Hunnisett's official assessments
LEGAL_CATEGORIES = [
    'court_order',
    'court_application_c2', 
    'court_application_c100',
    'position_statement',
    'witness_statement',
    'skeleton_argument',
    'cafcass_report',
    'social_work_report',
    'email_correspondence',
    'police_report',
    'POLICE_DISCLOSURE',
    'legislation',
    'bundle_index',
    'expert_report'  # Dr Hunnisett and other court-appointed experts
]

# Build SQL filter
category_filter = ', '.join([f"'{c}'" for c in LEGAL_CATEGORIES])

# Load only claims from legal documents and emails
cursor.execute(f"""
    SELECT c.id, c.claim_text, c.asserted_by,
           d.filename, d.document_category, d.title
    FROM claims c
    LEFT JOIN documents d ON c.document_id = d.id
    WHERE c.claim_text IS NOT NULL 
    AND LENGTH(c.claim_text) > 30
    AND d.document_category IN ({category_filter})
""")
claims = [dict(row) for row in cursor.fetchall()]

print("="*70)
print("LEGAL DOCUMENTS & EMAILS ONLY - ANALYSIS")
print("="*70)
print(f"\nLoaded {len(claims)} claims from legal documents and emails")

# Show breakdown
cursor.execute(f"""
    SELECT d.document_category, COUNT(*) as cnt
    FROM claims c
    LEFT JOIN documents d ON c.document_id = d.id
    WHERE c.claim_text IS NOT NULL 
    AND LENGTH(c.claim_text) > 30
    AND d.document_category IN ({category_filter})
    GROUP BY d.document_category
    ORDER BY cnt DESC
""")
print("\nDocument breakdown:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]} claims")

# ============================================================
# FIND TRUE CONTRADICTIONS
# ============================================================

TOPICS = {
    'conspiracy_involvement': {
        'name': 'Conspiracy to Murder - Knowledge/Involvement',
        'description': 'Whether Samantha and Paul Stephen knew about or were involved in the murder plan',
        'positive': ['conspired', 'involved in the planning', 'were aware', 'knew about the plan', 'encouraged', 'assisted'],
        'negative': ['did not conspire', 'no knowledge', 'not involved', 'had no idea', 'unaware of', 'no involvement'],
        'context': ['samantha', 'paul', 'stephen', 'murder', 'conspiracy'],
        'significance': 'CRITICAL',
        'legal_basis': 'Criminal law - conspiracy to murder; R v Gnango [2011]'
    },
    'threshold_criteria': {
        'name': 'Section 31 Threshold Criteria',
        'description': 'Whether the threshold for significant harm under Children Act 1989 s.31 is met',
        'positive': ['threshold is met', 'significant harm', 'threshold criteria satisfied', 'suffering harm', 'likely to suffer'],
        'negative': ['threshold not met', 'insufficient evidence for threshold', 'no significant harm', 'threshold not satisfied'],
        'context': None,
        'significance': 'HIGH',
        'legal_basis': 'Children Act 1989 s.31; Re B (Care Proceedings: Threshold Criteria) [2013]'
    },
    'living_location': {
        'name': 'Residence at Mildenhall',
        'description': 'Whether Samantha was truthful about living at RAF Mildenhall',
        'positive': ['living at mildenhall', 'lives at raf mildenhall', 'resided at mildenhall'],
        'negative': ['not living at mildenhall', 'was not true', 'lied about living'],
        'context': ['mildenhall', 'living', 'residence'],
        'significance': 'MEDIUM',
        'legal_basis': 'Credibility of witness - Lucas direction'
    },
    'parenting_capacity': {
        'name': 'Parenting Capacity Assessment',
        'description': 'Assessments of whether mother/stepfather can safely parent the children',
        'positive': ['able to parent', 'capable parent', 'meets the needs', 'appropriate care', 'protective'],
        'negative': ['unable to parent', 'risk to child', 'failed to protect', 'cannot meet needs', 'neglect'],
        'context': ['mother', 'samantha', 'paul', 'parent', 'care'],
        'significance': 'HIGH',
        'legal_basis': 'Children Act 1989 s.1 welfare checklist'
    },
    'credibility': {
        'name': 'Witness Credibility',
        'description': 'Assessments of whether the parents\' accounts are credible',
        'positive': ['credible', 'truthful', 'reliable witness', 'honest account'],
        'negative': ['not credible', 'lied', 'dishonest', 'unreliable', 'fabricated', 'untrue'],
        'context': ['mother', 'samantha', 'paul', 'respondent', 'account'],
        'significance': 'HIGH',
        'legal_basis': 'Lucas direction - R v Lucas [1981]'
    },
    'contact_recommendation': {
        'name': 'Contact Recommendation',
        'description': 'Whether contact between children and parents should continue',
        'positive': ['promote contact', 'beneficial contact', 'should have contact', 'maintain relationship'],
        'negative': ['no contact', 'suspend contact', 'contact refused', 'risk if contact', 'supervised only'],
        'context': ['contact', 'mother', 'father', 'children'],
        'significance': 'HIGH',
        'legal_basis': 'Children Act 1989 s.1(2A); Re C (Direct Contact: Suspension) [2011]'
    }
}

def find_topic_contradictions(claims, topic_config):
    positive_claims = []
    negative_claims = []
    
    for c in claims:
        text_lower = c['claim_text'].lower()
        
        if topic_config.get('context'):
            if not any(ctx in text_lower for ctx in topic_config['context']):
                continue
        
        for pos in topic_config['positive']:
            if pos in text_lower:
                positive_claims.append(c)
                break
        
        for neg in topic_config['negative']:
            if neg in text_lower:
                negative_claims.append(c)
                break
    
    return positive_claims, negative_claims

print("\n" + "="*70)
print("TRUE CONTRADICTIONS IN LEGAL DOCUMENTS")
print("="*70)

report = {
    'generated': datetime.now().isoformat(),
    'case_id': 'PE23C50095',
    'title': 'True Contradictions - Legal Documents & Emails Only',
    'description': 'Analysis limited to official court documents, position statements, and email correspondence',
    'total_claims_analyzed': len(claims),
    'document_types_included': LEGAL_CATEGORIES,
    'contradictions': [],
    'summary': {}
}

for topic_id, topic in TOPICS.items():
    pos_claims, neg_claims = find_topic_contradictions(claims, topic)
    
    if pos_claims or neg_claims:
        print(f"\n{'='*70}")
        print(f"[{topic['significance']}] {topic['name']}")
        print(f"{'='*70}")
        print(f"Description: {topic['description']}")
        print(f"Legal Basis: {topic['legal_basis']}")
        
        contradiction = {
            'id': topic_id,
            'topic': topic['name'],
            'description': topic['description'],
            'significance': topic['significance'],
            'legal_basis': topic['legal_basis'],
            'positive_claims': [],
            'negative_claims': [],
            'positive_count': len(pos_claims),
            'negative_count': len(neg_claims),
            'is_contradiction': bool(pos_claims and neg_claims)
        }
        
        if pos_claims:
            print(f"\n  Claims ASSERTING ({len(pos_claims)} total):")
            for c in pos_claims[:5]:
                print(f"    • \"{c['claim_text'][:100]}...\"")
                print(f"      Source: {c['filename']} ({c['document_category']})")
                contradiction['positive_claims'].append({
                    'text': c['claim_text'][:500],
                    'source': c['filename'],
                    'category': c['document_category']
                })
        
        if neg_claims:
            print(f"\n  Claims DENYING ({len(neg_claims)} total):")
            for c in neg_claims[:5]:
                print(f"    • \"{c['claim_text'][:100]}...\"")
                print(f"      Source: {c['filename']} ({c['document_category']})")
                contradiction['negative_claims'].append({
                    'text': c['claim_text'][:500],
                    'source': c['filename'],
                    'category': c['document_category']
                })
        
        if pos_claims and neg_claims:
            print(f"\n  *** CONTRADICTION: {len(pos_claims)} claims assert, {len(neg_claims)} claims deny ***")
        
        report['contradictions'].append(contradiction)
        report['summary'][topic_id] = {
            'topic': topic['name'],
            'positive': len(pos_claims),
            'negative': len(neg_claims),
            'significance': topic['significance'],
            'is_contradiction': bool(pos_claims and neg_claims)
        }

# ============================================================
# SOURCE CONSISTENCY ANALYSIS
# ============================================================

print("\n\n" + "="*70)
print("SOURCE CONSISTENCY - LEGAL DOCUMENTS ONLY")
print("="*70)

KNOWN_SOURCES = {
    'local_authority': ['local authority', 'cambridgeshire', 'la ', 'county council'],
    'cafcass': ['cafcass', 'children\'s guardian', 'guardian'],
    'court': ['court', 'judge', 'hhj', 'his honour', 'order'],
    'samantha_stephen': ['samantha', 'mrs stephen', 'sam ', 'respondent mother'],
    'paul_stephen': ['paul stephen', 'mr stephen', 'ssgt', 'stepfather'],
    'mandy_seamark': ['mandy', 'seamark', 'paternal grandmother', 'pgm'],
    'police': ['police', 'dci', 'dc ', 'constabulary', 'officer']
}

def identify_source(claim):
    text_lower = (claim['claim_text'] or '').lower()
    filename_lower = (claim['filename'] or '').lower()
    category = claim['document_category'] or ''
    
    for source_name, keywords in KNOWN_SOURCES.items():
        for kw in keywords:
            if kw in text_lower or kw in filename_lower:
                return source_name
    
    if 'police' in category.lower():
        return 'police'
    if 'social' in category.lower():
        return 'local_authority'
    if 'court' in category.lower():
        return 'court'
    if 'cafcass' in category.lower():
        return 'cafcass'
    if 'position' in category.lower():
        return 'party_submission'
    if 'email' in category.lower():
        return 'correspondence'
    
    return 'unknown'

claims_by_source = defaultdict(list)
for c in claims:
    source = identify_source(c)
    claims_by_source[source].append(c)

print("\nClaims by source (legal documents only):")
for source, source_claims in sorted(claims_by_source.items(), key=lambda x: -len(x[1])):
    print(f"  {source}: {len(source_claims)} claims")

# Check consistency within each source
CONSISTENCY_TOPICS = {
    'harm': {
        'positive': ['significant harm', 'harmed', 'at risk', 'suffered harm'],
        'negative': ['no harm', 'not harmed', 'safe', 'no concerns', 'no safeguarding']
    },
    'parenting': {
        'positive': ['good parent', 'capable', 'appropriate', 'meets needs'],
        'negative': ['unable', 'risk', 'failed', 'neglect', 'cannot']
    },
    'credibility': {
        'positive': ['credible', 'truthful', 'honest', 'reliable'],
        'negative': ['not credible', 'lied', 'dishonest', 'fabricated']
    }
}

source_consistency = []

for source, source_claims in claims_by_source.items():
    if len(source_claims) < 3:
        continue
    
    source_issues = []
    
    for topic_name, terms in CONSISTENCY_TOPICS.items():
        pos_claims = [c for c in source_claims if any(t in c['claim_text'].lower() for t in terms['positive'])]
        neg_claims = [c for c in source_claims if any(t in c['claim_text'].lower() for t in terms['negative'])]
        
        if pos_claims and neg_claims:
            source_issues.append({
                'topic': topic_name,
                'positive_examples': [c['claim_text'][:200] for c in pos_claims[:3]],
                'negative_examples': [c['claim_text'][:200] for c in neg_claims[:3]],
                'pos_count': len(pos_claims),
                'neg_count': len(neg_claims)
            })
    
    if source_issues:
        source_consistency.append({
            'source': source,
            'total_claims': len(source_claims),
            'inconsistencies': source_issues
        })
        
        print(f"\n{source.upper()} - Internal inconsistencies:")
        for issue in source_issues:
            print(f"  {issue['topic']}: {issue['pos_count']} positive vs {issue['neg_count']} negative")

# Add to report
report['source_consistency'] = source_consistency

# Save report
output_path = 'data/TRUE_CONTRADICTIONS_REPORT.json'
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

# Also update the source consistency report
with open('data/SOURCE_CONSISTENCY_REPORT.json', 'w', encoding='utf-8') as f:
    json.dump({
        'generated': datetime.now().isoformat(),
        'title': 'Source Consistency - Legal Documents Only',
        'document_types': LEGAL_CATEGORIES,
        'details': source_consistency
    }, f, indent=2, ensure_ascii=False)

print(f"\n\nReports saved:")
print(f"  - {output_path}")
print(f"  - data/SOURCE_CONSISTENCY_REPORT.json")

# Summary
print("\n" + "="*70)
print("SUMMARY")
print("="*70)
print(f"Total claims analyzed: {len(claims)}")
print(f"Document types included: {len(LEGAL_CATEGORIES)}")
contradictions_found = sum(1 for c in report['contradictions'] if c['is_contradiction'])
print(f"Contradictions found: {contradictions_found}")
print(f"Sources with internal inconsistencies: {len(source_consistency)}")

conn.close()

