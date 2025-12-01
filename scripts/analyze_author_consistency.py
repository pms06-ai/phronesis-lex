#!/usr/bin/env python3
"""
Analyze consistency of statements by each author/professional.
Find cases where the same person has made inconsistent or contradictory statements.
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

# Load all claims with author info
cursor.execute("""
    SELECT c.id, c.claim_text, c.asserted_by, c.modality, c.polarity,
           d.filename, d.document_category, d.title, d.document_date
    FROM claims c
    LEFT JOIN documents d ON c.document_id = d.id
    WHERE c.claim_text IS NOT NULL 
    AND LENGTH(c.claim_text) > 30
    AND c.asserted_by IS NOT NULL
    AND c.asserted_by != ''
""")
claims = [dict(row) for row in cursor.fetchall()]

print(f"Loaded {len(claims)} claims with known authors")

# Group claims by author
claims_by_author = defaultdict(list)
for c in claims:
    author = c['asserted_by'].strip().lower()
    # Normalize author names
    author = re.sub(r'\s+', ' ', author)
    claims_by_author[author].append(c)

print(f"Found {len(claims_by_author)} unique authors")

# Topics to check for consistency
CONSISTENCY_CHECKS = {
    'conspiracy_position': {
        'name': 'Position on Conspiracy Involvement',
        'asserting': ['conspired', 'involved', 'planned', 'knew about', 'aware of the plan', 'encouraged'],
        'denying': ['did not conspire', 'not involved', 'no knowledge', 'unaware', 'innocent']
    },
    'harm_assessment': {
        'name': 'Assessment of Harm to Children',
        'asserting': ['significant harm', 'suffered harm', 'at risk', 'harmed', 'traumatised', 'damaged'],
        'denying': ['no harm', 'not harmed', 'safe', 'thriving', 'doing well', 'no significant harm']
    },
    'parenting_view': {
        'name': 'View of Parenting Capacity',
        'positive': ['good parent', 'loving', 'capable', 'meets needs', 'appropriate', 'caring', 'protective'],
        'negative': ['poor parent', 'unable', 'risk', 'neglect', 'harmful', 'failed', 'cannot meet needs']
    },
    'credibility_view': {
        'name': 'View of Parent Credibility',
        'positive': ['credible', 'truthful', 'honest', 'reliable', 'believable'],
        'negative': ['not credible', 'lied', 'dishonest', 'fabricated', 'untrue', 'unreliable']
    },
    'contact_recommendation': {
        'name': 'Recommendation on Contact',
        'positive': ['should have contact', 'maintain contact', 'beneficial contact', 'promote contact', 'increase contact'],
        'negative': ['no contact', 'suspend contact', 'reduce contact', 'supervised only', 'risk if contact']
    },
    'placement_recommendation': {
        'name': 'Recommendation on Placement',
        'with_parents': ['return to mother', 'return to parents', 'rehabilitate', 'reunification', 'placed with mother'],
        'away_from_parents': ['remain in care', 'adoption', 'foster', 'special guardianship', 'cannot return']
    }
}

def check_topic_consistency(author_claims, topic_config):
    """Check if an author has made inconsistent statements on a topic."""
    positive_key = list(topic_config.keys())[1]  # First set of terms
    negative_key = list(topic_config.keys())[2]  # Second set of terms
    
    positive_terms = topic_config[positive_key]
    negative_terms = topic_config[negative_key]
    
    positive_statements = []
    negative_statements = []
    
    for c in author_claims:
        text_lower = c['claim_text'].lower()
        
        for term in positive_terms:
            if term in text_lower:
                positive_statements.append(c)
                break
        
        for term in negative_terms:
            if term in text_lower:
                negative_statements.append(c)
                break
    
    return positive_statements, negative_statements

# Analyze each author
author_analysis = {}
inconsistencies = []

# Focus on key professionals
KEY_AUTHORS = [
    'dci katie dounias', 'dci dounias', 'katie dounias',
    'dc 2072 atkinson', 'dc atkinson',
    'anna mayes', 
    'ben spencer',
    'carolyn dodson',
    'paul duggan',
    'mandy seamark', 'mandy jane seamark',
    'samantha stephen', 'samantha jane stephen',
    'paul stephen', 'paul m. stephen', 'ssgt paul stephen',
    'dr vivien wong-spracklen', 'dr wong-spracklen',
    'hhj gordon-saker', 'his honour judge gordon-saker',
    'lucy ardern',
    'local authority', 'cambridgeshire county council',
    'cafcass', 'children\'s guardian'
]

print("\n" + "="*70)
print("AUTHOR CONSISTENCY ANALYSIS")
print("="*70)

for author, author_claims in sorted(claims_by_author.items(), key=lambda x: -len(x[1])):
    # Skip if too few claims
    if len(author_claims) < 2:
        continue
    
    # Check if this is a key author
    is_key = any(key in author for key in KEY_AUTHORS)
    
    author_info = {
        'author': author,
        'total_claims': len(author_claims),
        'inconsistencies': [],
        'is_key_professional': is_key
    }
    
    # Check each topic for inconsistencies
    for topic_id, topic_config in CONSISTENCY_CHECKS.items():
        pos_statements, neg_statements = check_topic_consistency(author_claims, topic_config)
        
        if pos_statements and neg_statements:
            inconsistency = {
                'topic': topic_config['name'],
                'topic_id': topic_id,
                'positive_statements': [
                    {
                        'text': c['claim_text'][:300],
                        'source': c['filename'],
                        'date': c['document_date']
                    }
                    for c in pos_statements[:3]
                ],
                'negative_statements': [
                    {
                        'text': c['claim_text'][:300],
                        'source': c['filename'],
                        'date': c['document_date']
                    }
                    for c in neg_statements[:3]
                ],
                'positive_count': len(pos_statements),
                'negative_count': len(neg_statements)
            }
            author_info['inconsistencies'].append(inconsistency)
    
    if author_info['inconsistencies']:
        author_analysis[author] = author_info
        
        # If key professional, add to main inconsistencies list
        if is_key or len(author_info['inconsistencies']) > 1:
            inconsistencies.append(author_info)

# Sort by number of inconsistencies
inconsistencies.sort(key=lambda x: -len(x['inconsistencies']))

# Print results
print(f"\nFound {len(inconsistencies)} authors with internal inconsistencies")

for author_info in inconsistencies[:20]:
    author = author_info['author']
    print(f"\n{'='*70}")
    print(f"AUTHOR: {author.upper()}")
    print(f"Total claims: {author_info['total_claims']}")
    print(f"Inconsistencies found: {len(author_info['inconsistencies'])}")
    if author_info['is_key_professional']:
        print("*** KEY PROFESSIONAL ***")
    print("="*70)
    
    for inc in author_info['inconsistencies']:
        print(f"\n  Topic: {inc['topic']}")
        print(f"  {inc['positive_count']} statements one way, {inc['negative_count']} the other")
        
        print(f"\n  SAYS ONE THING:")
        for stmt in inc['positive_statements'][:2]:
            print(f"    \"{stmt['text'][:100]}...\"")
            print(f"    [Source: {stmt['source']}]")
        
        print(f"\n  BUT ALSO SAYS:")
        for stmt in inc['negative_statements'][:2]:
            print(f"    \"{stmt['text'][:100]}...\"")
            print(f"    [Source: {stmt['source']}]")

# Generate detailed report
report = {
    'generated': datetime.now().isoformat(),
    'case_id': 'PE23C50095',
    'title': 'Author Consistency Analysis',
    'description': 'Analysis of internal consistency in statements by each author/professional',
    'total_authors_analyzed': len(claims_by_author),
    'authors_with_inconsistencies': len(inconsistencies),
    'key_findings': [],
    'author_details': []
}

# Add key findings
for author_info in inconsistencies:
    if author_info['is_key_professional'] and author_info['inconsistencies']:
        for inc in author_info['inconsistencies']:
            report['key_findings'].append({
                'author': author_info['author'],
                'topic': inc['topic'],
                'significance': 'HIGH' if author_info['is_key_professional'] else 'MEDIUM',
                'positive_count': inc['positive_count'],
                'negative_count': inc['negative_count']
            })

# Add all author details
report['author_details'] = inconsistencies

# Save report
output_path = 'data/AUTHOR_CONSISTENCY_REPORT.json'
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

print(f"\n\nFull report saved to: {output_path}")

# Also create a summary for the dashboard
summary = {
    'total_authors': len(claims_by_author),
    'authors_with_issues': len(inconsistencies),
    'key_professional_issues': len([a for a in inconsistencies if a['is_key_professional']]),
    'top_inconsistent_authors': [
        {
            'name': a['author'],
            'claims': a['total_claims'],
            'issues': len(a['inconsistencies']),
            'key': a['is_key_professional']
        }
        for a in inconsistencies[:10]
    ]
}

with open('data/author_consistency_summary.json', 'w', encoding='utf-8') as f:
    json.dump(summary, f, indent=2)

print(f"Summary saved to: data/author_consistency_summary.json")
conn.close()

