"""List all case numbers currently being tracked in the database."""
import sqlite3
from collections import defaultdict

conn = sqlite3.connect('Phronesis/data/db/phronesis.db')
cursor = conn.cursor()

print("="*70)
print("CASES CURRENTLY TRACKED IN PHRONESIS DATABASE")
print("="*70)

# Get all distinct case IDs from documents
cursor.execute("""
    SELECT DISTINCT case_id, COUNT(*) as doc_count 
    FROM documents 
    WHERE case_id IS NOT NULL 
    GROUP BY case_id
""")
doc_cases = cursor.fetchall()

# Get all distinct case IDs from claims
cursor.execute("""
    SELECT DISTINCT case_id, COUNT(*) as claim_count 
    FROM claims 
    WHERE case_id IS NOT NULL 
    GROUP BY case_id
""")
claim_cases = {row[0]: row[1] for row in cursor.fetchall()}

# Get all distinct case IDs from entities
cursor.execute("""
    SELECT DISTINCT case_id, COUNT(*) as entity_count 
    FROM entities 
    WHERE case_id IS NOT NULL 
    GROUP BY case_id
""")
entity_cases = {row[0]: row[1] for row in cursor.fetchall()}

# Check if there's a cases table
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cases'")
has_cases_table = cursor.fetchone() is not None

if has_cases_table:
    cursor.execute("SELECT * FROM cases")
    cases = cursor.fetchall()
    if cases:
        print("\nFrom CASES table:")
        cursor.execute("PRAGMA table_info(cases)")
        columns = [c[1] for c in cursor.fetchall()]
        for case in cases:
            print(f"  {dict(zip(columns, case))}")

print("\nCASE SUMMARY:")
print("-"*70)

all_case_ids = set()
for case_id, _ in doc_cases:
    all_case_ids.add(case_id)
for case_id in claim_cases:
    all_case_ids.add(case_id)
for case_id in entity_cases:
    all_case_ids.add(case_id)

for case_id in sorted(all_case_ids):
    doc_count = next((d[1] for d in doc_cases if d[0] == case_id), 0)
    claim_count = claim_cases.get(case_id, 0)
    entity_count = entity_cases.get(case_id, 0)
    
    print(f"\nCase: {case_id}")
    print(f"  Documents: {doc_count}")
    print(f"  Claims: {claim_count}")
    print(f"  Entities: {entity_count}")

# Get document categories for each case
print("\n" + "="*70)
print("DOCUMENT BREAKDOWN BY CATEGORY")
print("="*70)

for case_id in sorted(all_case_ids):
    cursor.execute("""
        SELECT document_category, COUNT(*) 
        FROM documents 
        WHERE case_id = ? 
        GROUP BY document_category
        ORDER BY COUNT(*) DESC
    """, (case_id,))
    categories = cursor.fetchall()
    
    if categories:
        print(f"\n{case_id}:")
        for cat, count in categories:
            print(f"  {cat or 'UNCATEGORIZED'}: {count}")

# Get date range of documents
print("\n" + "="*70)
print("DATE RANGE OF DOCUMENTS")
print("="*70)

for case_id in sorted(all_case_ids):
    cursor.execute("""
        SELECT MIN(document_date), MAX(document_date) 
        FROM documents 
        WHERE case_id = ? AND document_date IS NOT NULL
    """, (case_id,))
    date_range = cursor.fetchone()
    
    if date_range and date_range[0]:
        print(f"\n{case_id}: {date_range[0]} to {date_range[1]}")

conn.close()

