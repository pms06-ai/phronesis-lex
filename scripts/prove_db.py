"""Prove database has real data."""
import sqlite3

conn = sqlite3.connect('Phronesis/data/db/phronesis.db')
c = conn.cursor()

print('='*70)
print('DATABASE PROOF - LIVE QUERIES')
print('='*70)

# Count tables
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in c.fetchall()]
print(f'\nTables in database: {len(tables)}')
print(f'Tables: {tables}')

# Count documents
c.execute('SELECT COUNT(*) FROM documents')
print(f'\nDocuments: {c.fetchone()[0]}')

# Count claims
c.execute('SELECT COUNT(*) FROM claims')
print(f'Claims: {c.fetchone()[0]}')

# Count cases
c.execute('SELECT COUNT(*) FROM cases')
print(f'Cases: {c.fetchone()[0]}')

# Count entities
c.execute('SELECT COUNT(*) FROM entities')
print(f'Entities: {c.fetchone()[0]}')

# Show sample cases
print('\n' + '='*70)
print('SAMPLE CASES IN DATABASE')
print('='*70)
c.execute('SELECT reference, title, status FROM cases LIMIT 7')
for row in c.fetchall():
    title = row[1][:50] if row[1] else 'N/A'
    print(f'  {row[0]}: {title}... [{row[2]}]')

# Show sample claims
print('\n' + '='*70)
print('SAMPLE CLAIMS (first 5)')
print('='*70)
c.execute('SELECT claim_text, asserted_by FROM claims WHERE claim_text IS NOT NULL LIMIT 5')
for i, row in enumerate(c.fetchall(), 1):
    text = row[0][:80] if row[0] else 'N/A'
    author = row[1] or 'Unknown'
    print(f'{i}. [{author}] "{text}..."')

# Show document categories
print('\n' + '='*70)
print('DOCUMENTS BY CATEGORY')
print('='*70)
c.execute('SELECT document_category, COUNT(*) FROM documents GROUP BY document_category ORDER BY COUNT(*) DESC LIMIT 10')
for row in c.fetchall():
    print(f'  {row[0] or "unknown"}: {row[1]}')

# Show sample murder-related claims
print('\n' + '='*70)
print('MURDER-RELATED CLAIMS (sample)')
print('='*70)
c.execute("SELECT claim_text FROM claims WHERE LOWER(claim_text) LIKE '%murder%' OR LOWER(claim_text) LIKE '%dunmore%' LIMIT 5")
for i, row in enumerate(c.fetchall(), 1):
    text = row[0][:100] if row[0] else 'N/A'
    print(f'{i}. "{text}..."')

conn.close()

