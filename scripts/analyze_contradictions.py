#!/usr/bin/env python3
"""
Analyze contradiction report to verify quality of detections.
"""

import json

# Load the report
with open('data/contradiction_report_PE23C50095.json', encoding='utf-8') as f:
    data = json.load(f)

print("="*70)
print("CONTRADICTION ANALYSIS - Quality Check")
print("="*70)
print(f"\nTotal contradictions: {data['total_contradictions']}")
print(f"By type: {data['by_type']}")
print(f"By severity: {data['by_severity']}")

# Analyze self-contradictions (most valuable)
print("\n" + "="*70)
print("SELF-CONTRADICTIONS (Same author contradicting themselves)")
print("These are CRITICAL - same person saying opposite things")
print("="*70)
self_contradictions = [x for x in data['contradictions'] if x['type'] == 'self_contradiction']
for i, c in enumerate(self_contradictions[:10], 1):
    author = c.get('author_a') or c.get('claim_a_author') or 'Unknown'
    text_a = c.get('text_a') or c.get('claim_a_text') or ''
    text_b = c.get('text_b') or c.get('claim_b_text') or ''
    print(f"\n#{i} Author: {author}")
    print(f"   CLAIM A: \"{text_a[:150]}...\"")
    print(f"   CLAIM B: \"{text_b[:150]}...\"")

# Analyze direct contradictions
print("\n" + "="*70)
print("DIRECT CONTRADICTIONS (Different authors, opposite claims)")
print("="*70)
direct = [x for x in data['contradictions'] if x['type'] == 'direct']
for i, c in enumerate(direct[:10], 1):
    author_a = c.get('author_a') or c.get('claim_a_author') or 'Unknown'
    author_b = c.get('author_b') or c.get('claim_b_author') or 'Unknown'
    text_a = c.get('text_a') or c.get('claim_a_text') or ''
    text_b = c.get('text_b') or c.get('claim_b_text') or ''
    print(f"\n#{i}")
    print(f"   {author_a}: \"{text_a[:120]}...\"")
    print(f"   {author_b}: \"{text_b[:120]}...\"")

# Analyze value contradictions - these might be false positives
print("\n" + "="*70)
print("VALUE CONTRADICTIONS (Sample - checking for false positives)")
print("="*70)
value = [x for x in data['contradictions'] if x['type'] == 'value']
print(f"Total value contradictions: {len(value)}")
print("\nSample of 5:")
for i, c in enumerate(value[:5], 1):
    text_a = c.get('text_a') or c.get('claim_a_text') or ''
    text_b = c.get('text_b') or c.get('claim_b_text') or ''
    sim = c.get('semantic_similarity', 0)
    print(f"\n#{i} (similarity: {sim:.2f})")
    print(f"   A: \"{text_a[:100]}...\"")
    print(f"   B: \"{text_b[:100]}...\"")

# Check attribution contradictions
print("\n" + "="*70)
print("ATTRIBUTION CONTRADICTIONS")
print("="*70)
attribution = [x for x in data['contradictions'] if x['type'] == 'attribution']
for i, c in enumerate(attribution[:5], 1):
    author_a = c.get('author_a') or c.get('claim_a_author') or 'Unknown'
    author_b = c.get('author_b') or c.get('claim_b_author') or 'Unknown'
    text_a = c.get('text_a') or c.get('claim_a_text') or ''
    text_b = c.get('text_b') or c.get('claim_b_text') or ''
    print(f"\n#{i}")
    print(f"   {author_a}: \"{text_a[:120]}...\"")
    print(f"   {author_b}: \"{text_b[:120]}...\"")

