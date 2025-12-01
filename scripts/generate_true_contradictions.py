#!/usr/bin/env python3
"""
Generate a report of TRUE contradictions - where claims actually conflict.
"""

import sqlite3
import json
import re
from datetime import datetime

db_path = 'Phronesis/data/db/phronesis.db'
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Load all claims with source info
cursor.execute("""
    SELECT c.id, c.claim_text, c.asserted_by, c.modality, c.polarity,
           d.filename, d.document_category, d.title
    FROM claims c
    LEFT JOIN documents d ON c.document_id = d.id
    WHERE c.claim_text IS NOT NULL AND LENGTH(c.claim_text) > 30
""")
claims = [dict(row) for row in cursor.fetchall()]

def find_topic_contradictions(claims, topic_name, positive_terms, negative_terms, context_terms=None):
    """Find claims that contradict each other on a specific topic."""
    positive_claims = []
    negative_claims = []
    
    for c in claims:
        text_lower = c['claim_text'].lower()
        
        # Check if claim is about the right context
        if context_terms:
            if not any(ctx in text_lower for ctx in context_terms):
                continue
        
        # Check for positive assertions
        for pos in positive_terms:
            if pos in text_lower:
                positive_claims.append(c)
                break
        
        # Check for negative assertions
        for neg in negative_terms:
            if neg in text_lower:
                negative_claims.append(c)
                break
    
    return positive_claims, negative_claims

# Define contradiction topics
TOPICS = {
    'conspiracy_involvement': {
        'name': 'Conspiracy to Murder - Knowledge/Involvement',
        'description': 'Whether Samantha and Paul Stephen knew about or were involved in the plan to murder Joshua and Gary Dunmore',
        'positive': ['conspired', 'involved in the planning', 'were aware', 'knew about the plan', 'encouraged', 'assisted', 'working hypothesis'],
        'negative': ['did not conspire', 'no knowledge', 'not involved', 'had no idea', 'unaware of'],
        'context': ['samantha', 'paul', 'stephen', 'murder', 'conspiracy'],
        'significance': 'CRITICAL',
        'legal_basis': 'Criminal law - conspiracy to murder; R v Gnango [2011]'
    },
    'threshold_criteria': {
        'name': 'Section 31 Threshold Criteria',
        'description': 'Whether the threshold for significant harm under Children Act 1989 s.31 is met',
        'positive': ['threshold is met', 'significant harm', 'threshold criteria satisfied', 'suffering harm', 'likely to suffer'],
        'negative': ['threshold not met', 'insufficient evidence for threshold', 'no significant harm'],
        'context': None,
        'significance': 'HIGH',
        'legal_basis': 'Children Act 1989 s.31; Re B (Care Proceedings: Threshold Criteria) [2013]'
    },
    'living_location': {
        'name': 'Residence at Mildenhall',
        'description': 'Whether Samantha was truthful about living at RAF Mildenhall',
        'positive': ['living at mildenhall', 'lives at raf mildenhall', 'resided at mildenhall', 'currently lives'],
        'negative': ['not living at mildenhall', 'was not true', 'lied about', 'did not reside'],
        'context': ['mildenhall', 'living', 'residence'],
        'significance': 'MEDIUM',
        'legal_basis': 'Credibility of witness - Lucas direction'
    },
    'parenting_capacity': {
        'name': 'Parenting Capacity',
        'description': 'Assessments of whether mother/stepfather can safely parent',
        'positive': ['able to parent', 'capable', 'meets the needs', 'loving', 'good care', 'appropriate care'],
        'negative': ['unable to parent', 'risk to child', 'failed to protect', 'harmful', 'neglect', 'cannot meet needs'],
        'context': ['mother', 'samantha', 'paul', 'parent', 'care'],
        'significance': 'HIGH',
        'legal_basis': 'Children Act 1989 s.1 welfare checklist'
    },
    'credibility': {
        'name': 'Witness Credibility',
        'description': 'Assessments of whether parents\' accounts are credible',
        'positive': ['credible', 'truthful', 'reliable', 'honest account'],
        'negative': ['not credible', 'lied', 'dishonest', 'unreliable', 'fabricated', 'untrue', 'false'],
        'context': ['mother', 'samantha', 'paul', 'respondent', 'account', 'evidence'],
        'significance': 'HIGH',
        'legal_basis': 'Lucas direction - R v Lucas [1981]'
    },
    'nfa_outcome': {
        'name': 'Criminal Investigation Outcome',
        'description': 'Status and outcome of the criminal investigation',
        'positive': ['arrested', 'suspect', 'charged', 'investigation ongoing', 'under investigation'],
        'negative': ['no further action', 'nfa', 'released', 'insufficient evidence', 'not charged', 'cleared'],
        'context': ['samantha', 'paul', 'stephen', 'police', 'investigation'],
        'significance': 'CRITICAL',
        'legal_basis': 'PACE 1984; CPS charging standards'
    }
}

# Find contradictions for each topic
report = {
    'generated': datetime.now().isoformat(),
    'case_id': 'PE23C50095',
    'title': 'True Contradictions Report',
    'description': 'Genuine contradictory claims identified in case documents',
    'contradictions': [],
    'summary': {}
}

for topic_id, topic in TOPICS.items():
    pos_claims, neg_claims = find_topic_contradictions(
        claims,
        topic['name'],
        topic['positive'],
        topic['negative'],
        topic.get('context')
    )
    
    if pos_claims and neg_claims:
        contradiction = {
            'id': topic_id,
            'topic': topic['name'],
            'description': topic['description'],
            'significance': topic['significance'],
            'legal_basis': topic['legal_basis'],
            'positive_claims': [
                {
                    'text': c['claim_text'][:500],
                    'author': c['asserted_by'],
                    'source': c['filename'] or c['title'],
                    'category': c['document_category']
                }
                for c in pos_claims[:10]  # Limit to top 10
            ],
            'negative_claims': [
                {
                    'text': c['claim_text'][:500],
                    'author': c['asserted_by'],
                    'source': c['filename'] or c['title'],
                    'category': c['document_category']
                }
                for c in neg_claims[:10]
            ],
            'positive_count': len(pos_claims),
            'negative_count': len(neg_claims)
        }
        report['contradictions'].append(contradiction)
        report['summary'][topic_id] = {
            'topic': topic['name'],
            'positive': len(pos_claims),
            'negative': len(neg_claims),
            'significance': topic['significance']
        }

# Save the report
output_path = 'data/TRUE_CONTRADICTIONS_REPORT.json'
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

# Print summary
print("="*70)
print("TRUE CONTRADICTIONS REPORT")
print("="*70)
print(f"\nGenerated: {report['generated']}")
print(f"Total contradiction topics: {len(report['contradictions'])}")

for c in report['contradictions']:
    print(f"\n{'='*70}")
    print(f"[{c['significance']}] {c['topic']}")
    print(f"{'='*70}")
    print(f"Description: {c['description']}")
    print(f"Legal Basis: {c['legal_basis']}")
    print(f"\n  Claims ASSERTING ({c['positive_count']} total):")
    for claim in c['positive_claims'][:3]:
        print(f"    • [{claim['author'] or 'Unknown'}] \"{claim['text'][:100]}...\"")
        print(f"      Source: {claim['source']} ({claim['category']})")
    
    print(f"\n  Claims DENYING ({c['negative_count']} total):")
    for claim in c['negative_claims'][:3]:
        print(f"    • [{claim['author'] or 'Unknown'}] \"{claim['text'][:100]}...\"")
        print(f"      Source: {claim['source']} ({claim['category']})")

print(f"\n\nFull report saved to: {output_path}")
conn.close()

