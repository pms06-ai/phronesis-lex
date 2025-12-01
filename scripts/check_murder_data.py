"""Check that murder investigation data was ingested properly."""
import sqlite3
from pathlib import Path

conn = sqlite3.connect('Phronesis/data/db/phronesis.db')
cursor = conn.cursor()

# Count documents
cursor.execute('SELECT COUNT(*) FROM documents')
doc_count = cursor.fetchone()[0]

# Count claims
cursor.execute('SELECT COUNT(*) FROM claims')
claim_count = cursor.fetchone()[0]

# Count murder-related claims
cursor.execute("""SELECT COUNT(*) FROM claims 
    WHERE context LIKE '%Murder%' OR claim_text LIKE '%murder%'
    OR claim_text LIKE '%Alderton%' OR claim_text LIKE '%Dunmore%'""")
murder_claims = cursor.fetchone()[0]

# Count entities
cursor.execute('SELECT COUNT(*) FROM entities')
entity_count = cursor.fetchone()[0]

print(f'Total documents: {doc_count}')
print(f'Total claims: {claim_count}')
print(f'Murder investigation claims: {murder_claims}')
print(f'Total entities: {entity_count}')

# Show the murder investigation document
cursor.execute("""SELECT title, document_category, document_date 
    FROM documents WHERE title LIKE '%Operation Scan%'""")
doc = cursor.fetchone()
if doc:
    print(f'\nMurder investigation doc: {doc[0]}')
    print(f'  Category: {doc[1]}')
    print(f'  Date: {doc[2]}')

# Show some murder-related claims
print('\n' + '='*60)
print('SAMPLE MURDER INVESTIGATION CLAIMS:')
print('='*60)
cursor.execute("""
    SELECT claim_text, asserted_by, date_made, modality 
    FROM claims 
    WHERE claim_text LIKE '%Alderton%' 
    OR claim_text LIKE '%Joshua%' 
    OR claim_text LIKE '%murder%'
    LIMIT 10
""")
for row in cursor.fetchall():
    print(f'\n[{row[3]}] {row[1]} ({row[2]}):')
    print(f'  "{row[0][:100]}..."' if len(row[0]) > 100 else f'  "{row[0]}"')

conn.close()

