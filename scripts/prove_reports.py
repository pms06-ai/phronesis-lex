"""Prove reports have real data."""
import json

# Contradiction report
print('='*70)
print('CONTRADICTION REPORT')
print('='*70)
with open('data/contradiction_report_PE23C50095.json', encoding='utf-8') as f:
    d = json.load(f)
print(f'Total contradictions: {d["total_contradictions"]}')
print(f'By severity: {d["by_severity"]}')
print(f'By type: {d["by_type"]}')

# Show sample contradictions
print('\nSample contradictions:')
for i, c in enumerate(d.get('contradictions', [])[:3], 1):
    ctype = c.get('contradiction_type', c.get('type', 'unknown'))
    print(f'{i}. Type: {ctype}')
    print(f'   Author A: {c.get("claim_a_author", c.get("author_a", "Unknown"))}')
    a_text = c.get("claim_a_text", c.get("text_a", "N/A"))[:70]
    b_text = c.get("claim_b_text", c.get("text_b", "N/A"))[:70]
    print(f'   Claim A: "{a_text}..."')
    print(f'   Claim B: "{b_text}..."')
    print()

# Accountability audit
print('='*70)
print('ACCOUNTABILITY AUDIT REPORT')
print('='*70)
with open('data/accountability_audit_report.json', encoding='utf-8') as f:
    d = json.load(f)
print(f'Total breaches: {d["total_breaches"]}')
print(f'\nBreaches by agency:')
for agency, data in d['agency_results'].items():
    breach_count = len(data.get('breaches', []))
    print(f'  {agency}: {breach_count} breaches')

# Show sample breaches
print('\nSample police breaches:')
police = d['agency_results'].get('police', {})
for i, b in enumerate(police.get('breaches', [])[:3], 1):
    print(f'{i}. {b["duty_title"]}')
    print(f'   Indicator: {b["indicator"]}')
    print(f'   Severity: {b["severity"]}')
    print(f'   Evidence count: {b["evidence_count"]}')
    print()

# Legal arguments
print('='*70)
print('LEGAL ARGUMENTS')
print('='*70)
with open('data/analysis/legal_arguments.json', encoding='utf-8') as f:
    d = json.load(f)
print(f'Total arguments: {d["total_arguments"]}')
print(f'\nBy agency:')
for agency, args in d['by_agency'].items():
    print(f'  {agency}: {len(args)} arguments')

