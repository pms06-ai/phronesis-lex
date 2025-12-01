#!/usr/bin/env python3
"""
Analyze consistency by document source and extract authors from claim text.
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

# Load claims with document info
cursor.execute("""
    SELECT c.id, c.claim_text, c.asserted_by,
           d.filename, d.document_category, d.title
    FROM claims c
    LEFT JOIN documents d ON c.document_id = d.id
    WHERE c.claim_text IS NOT NULL AND LENGTH(c.claim_text) > 30
""")
claims = [dict(row) for row in cursor.fetchall()]

print(f"Loaded {len(claims)} claims")

# Extract potential authors from claim text
def extract_author_from_text(text):
    """Extract who is making or being quoted in a claim."""
    text_lower = text.lower()
    
    # Patterns for quoted speech
    patterns = [
        (r"(\w+(?:\s+\w+)?)\s+(?:said|stated|reported|claims|alleges|submits)", 1),
        (r"according to (\w+(?:\s+\w+)?)", 1),
        (r"(\w+(?:\s+\w+)?)\s+told (?:the court|us|me)", 1),
        (r"dr\.?\s+(\w+)", 0),  # Dr. Name
        (r"(?:mr|mrs|ms)\.?\s+(\w+)", 0),  # Mr/Mrs/Ms Name
    ]
    
    for pattern, _ in patterns:
        match = re.search(pattern, text_lower)
        if match:
            return match.group(1).strip()
    
    return None

# Known authors/sources to track
KNOWN_SOURCES = {
    'local authority': ['local authority', 'cambridgeshire', 'la ', 'county council'],
    'cafcass': ['cafcass', 'children\'s guardian', 'guardian'],
    'police': ['police', 'dci', 'dc ', 'constabulary', 'officer'],
    'court': ['court', 'judge', 'hhj', 'his honour'],
    'samantha stephen': ['samantha', 'mrs stephen', 'sam ', 'respondent mother'],
    'paul stephen': ['paul stephen', 'mr stephen', 'ssgt stephen', 'stepfather'],
    'mandy seamark': ['mandy', 'seamark', 'paternal grandmother', 'pgm'],
    'joshua dunmore': ['joshua', 'josh ', 'father', 'mr dunmore'],
    'social worker': ['social worker', 'sw ', 'fran balmford', 'anna mayes'],
    'expert': ['dr ', 'expert', 'psychologist', 'psychiatrist', 'wong-spracklen']
}

def identify_source(claim):
    """Identify the likely source of a claim."""
    text_lower = (claim['claim_text'] or '').lower()
    filename_lower = (claim['filename'] or '').lower()
    category_lower = (claim['document_category'] or '').lower()
    
    for source_name, keywords in KNOWN_SOURCES.items():
        for kw in keywords:
            if kw in text_lower or kw in filename_lower:
                return source_name
    
    # Fall back to document category
    if 'police' in category_lower:
        return 'police'
    if 'social' in category_lower or 'la' in category_lower:
        return 'local authority'
    if 'court' in category_lower:
        return 'court'
    if 'cafcass' in category_lower:
        return 'cafcass'
    if 'expert' in category_lower:
        return 'expert'
    
    return 'unknown'

# Group claims by source
claims_by_source = defaultdict(list)
for c in claims:
    source = identify_source(c)
    claims_by_source[source].append(c)

print(f"\nClaims by source:")
for source, source_claims in sorted(claims_by_source.items(), key=lambda x: -len(x[1])):
    print(f"  {source}: {len(source_claims)} claims")

# Now check for contradictions within each source
TOPICS = {
    'conspiracy': {
        'asserting': ['conspired', 'involved', 'planned', 'knew', 'aware', 'encouraged'],
        'denying': ['did not conspire', 'not involved', 'no knowledge', 'innocent', 'unaware']
    },
    'harm': {
        'asserting': ['significant harm', 'harmed', 'at risk', 'suffered', 'traumatised'],
        'denying': ['no harm', 'not harmed', 'safe', 'no risk', 'thriving']
    },
    'parenting': {
        'positive': ['good parent', 'capable', 'loving', 'meets needs', 'appropriate'],
        'negative': ['poor parent', 'unable', 'risk', 'neglect', 'failed']
    },
    'credibility': {
        'positive': ['credible', 'truthful', 'honest', 'reliable'],
        'negative': ['not credible', 'lied', 'dishonest', 'fabricated']
    },
    'return_children': {
        'for': ['return to mother', 'rehabilitate', 'reunification', 'restore'],
        'against': ['remain in care', 'adoption', 'cannot return', 'special guardianship']
    }
}

print("\n" + "="*70)
print("ANALYZING SOURCE CONSISTENCY")
print("="*70)

inconsistencies = []

for source, source_claims in claims_by_source.items():
    if len(source_claims) < 5:
        continue
    
    source_inconsistencies = []
    
    for topic_name, topic_terms in TOPICS.items():
        keys = list(topic_terms.keys())
        pos_terms = topic_terms[keys[0]]
        neg_terms = topic_terms[keys[1]]
        
        pos_claims = []
        neg_claims = []
        
        for c in source_claims:
            text_lower = c['claim_text'].lower()
            
            if any(term in text_lower for term in pos_terms):
                pos_claims.append(c)
            if any(term in text_lower for term in neg_terms):
                neg_claims.append(c)
        
        if pos_claims and neg_claims:
            source_inconsistencies.append({
                'topic': topic_name,
                'positive_examples': [c['claim_text'][:200] for c in pos_claims[:3]],
                'negative_examples': [c['claim_text'][:200] for c in neg_claims[:3]],
                'pos_count': len(pos_claims),
                'neg_count': len(neg_claims)
            })
    
    if source_inconsistencies:
        inconsistencies.append({
            'source': source,
            'total_claims': len(source_claims),
            'inconsistencies': source_inconsistencies
        })

# Print results
for inc in inconsistencies:
    print(f"\n{'='*70}")
    print(f"SOURCE: {inc['source'].upper()}")
    print(f"Total claims: {inc['total_claims']}")
    print(f"Internal inconsistencies: {len(inc['inconsistencies'])}")
    print("="*70)
    
    for topic_inc in inc['inconsistencies']:
        print(f"\n  Topic: {topic_inc['topic'].upper()}")
        print(f"  {topic_inc['pos_count']} claims one way, {topic_inc['neg_count']} the other")
        
        print("\n  CLAIMS ASSERTING:")
        for ex in topic_inc['positive_examples'][:2]:
            print(f"    \"{ex[:100]}...\"")
        
        print("\n  CLAIMS DENYING:")
        for ex in topic_inc['negative_examples'][:2]:
            print(f"    \"{ex[:100]}...\"")

# Save report
report = {
    'generated': datetime.now().isoformat(),
    'title': 'Source Consistency Analysis',
    'sources_analyzed': len(claims_by_source),
    'sources_with_inconsistencies': len(inconsistencies),
    'details': inconsistencies
}

with open('data/SOURCE_CONSISTENCY_REPORT.json', 'w', encoding='utf-8') as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

print(f"\n\nReport saved to: data/SOURCE_CONSISTENCY_REPORT.json")

# Create a human-readable summary
print("\n" + "="*70)
print("SUMMARY: KEY INTERNAL CONTRADICTIONS BY SOURCE")
print("="*70)

for inc in inconsistencies:
    if len(inc['inconsistencies']) > 0:
        source = inc['source']
        topics = [i['topic'] for i in inc['inconsistencies']]
        print(f"\n{source.upper()}:")
        print(f"  Claims: {inc['total_claims']}")
        print(f"  Inconsistent on: {', '.join(topics)}")
        
        # Show the most significant
        for topic_inc in inc['inconsistencies'][:2]:
            print(f"\n  {topic_inc['topic'].upper()}:")
            print(f"    Says: \"{topic_inc['positive_examples'][0][:80]}...\"")
            print(f"    But also: \"{topic_inc['negative_examples'][0][:80]}...\"")

conn.close()

