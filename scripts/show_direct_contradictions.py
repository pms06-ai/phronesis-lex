"""Show direct contradictions from the report."""
import json

with open('data/contradiction_report_PE23C50095.json', 'r', encoding='utf-8') as f:
    report = json.load(f)

print('=' * 70)
print('DIRECT CONTRADICTIONS')
print('Different authors making opposite claims about the same things')
print('=' * 70)
print()

# Get direct contradictions where authors are different
direct = [c for c in report['contradictions'] 
          if c['type'] == 'direct' and not c.get('same_author', False)]

if not direct:
    # Also check high severity ones
    high = [c for c in report['contradictions'] 
            if c['severity'] == 'high' and not c.get('same_author', False)]
    direct = high

print(f"Found {len(direct)} direct contradictions\n")

for i, c in enumerate(direct[:15], 1):
    author_a = c.get('author_a') or c.get('source_a') or 'Unknown'
    author_b = c.get('author_b') or c.get('source_b') or 'Unknown'
    
    print(f"#{i}")
    print(f"   {author_a} vs {author_b}")
    
    if c.get('text_a'):
        text_a = c['text_a'][:100] + '...' if len(c['text_a']) > 100 else c['text_a']
        print(f"   A says: \"{text_a}\"")
    
    if c.get('text_b'):
        text_b = c['text_b'][:100] + '...' if len(c['text_b']) > 100 else c['text_b']
        print(f"   B says: \"{text_b}\"")
    
    print()

print('=' * 70)
print('ATTRIBUTION DISPUTES')
print('=' * 70)
print()

attribution = [c for c in report['contradictions'] if c['type'] == 'attribution']
print(f"Found {len(attribution)} attribution disputes\n")

for i, c in enumerate(attribution[:10], 1):
    author_a = c.get('author_a') or c.get('source_a') or 'Unknown'
    author_b = c.get('author_b') or c.get('source_b') or 'Unknown'
    
    print(f"#{i}")
    print(f"   {author_a} vs {author_b}")
    
    if c.get('text_a'):
        text_a = c['text_a'][:100] + '...' if len(c['text_a']) > 100 else c['text_a']
        print(f"   A says: \"{text_a}\"")
    
    if c.get('text_b'):
        text_b = c['text_b'][:100] + '...' if len(c['text_b']) > 100 else c['text_b']
        print(f"   B says: \"{text_b}\"")
    
    print()

# Summary by author pairs
print('=' * 70)
print('CONFLICT PAIRS (authors most frequently in disagreement)')
print('=' * 70)
print()

pairs = {}
for c in report['contradictions']:
    if not c.get('same_author', False):
        a = c.get('author_a') or c.get('source_a') or 'Unknown'
        b = c.get('author_b') or c.get('source_b') or 'Unknown'
        pair = tuple(sorted([a, b]))
        pairs[pair] = pairs.get(pair, 0) + 1

sorted_pairs = sorted(pairs.items(), key=lambda x: -x[1])[:20]
for (a, b), count in sorted_pairs:
    print(f"  {a} vs {b}: {count} conflicts")

