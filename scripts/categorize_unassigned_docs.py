"""
Review and categorize the 446 unassigned documents.
"""
import sqlite3
import re
import json
from datetime import datetime
from uuid import uuid4
from collections import defaultdict

conn = sqlite3.connect('Phronesis/data/db/phronesis.db')
cursor = conn.cursor()

# Get the case UUIDs
cursor.execute("SELECT id, reference FROM cases")
case_map = {row[1]: row[0] for row in cursor.fetchall()}

# Main case UUID for general documents
main_case_uuid = case_map.get('PE23C50095')

print("="*70)
print("ANALYZING 446 UNASSIGNED DOCUMENTS")
print("="*70)

# Get unassigned documents (those not matching any specific case pattern)
# These are documents that weren't updated in the previous script
cursor.execute("""
    SELECT id, filename, title, document_category, raw_text, file_type
    FROM documents 
    WHERE case_id = ?
""", (main_case_uuid,))

# Actually, let's get ALL documents and check which ones don't have specific case refs
cursor.execute("""
    SELECT d.id, d.filename, d.title, d.document_category, 
           SUBSTR(d.raw_text, 1, 2000) as text_preview, d.file_type,
           c.reference as current_case
    FROM documents d
    LEFT JOIN cases c ON d.case_id = c.id
""")

documents = cursor.fetchall()

# Categorization rules
categories = {
    'LEGISLATION': [],
    'CAFCASS_REPORTS': [],
    'SOCIAL_WORK': [],
    'MEDICAL': [],
    'POLICE': [],
    'COURT_ORDERS': [],
    'EXPERT_REPORTS': [],
    'CORRESPONDENCE': [],
    'SCHOOL_RECORDS': [],
    'WITNESS_STATEMENTS': [],
    'POSITION_STATEMENTS': [],
    'SKELETON_ARGUMENTS': [],
    'BUNDLES_INDEX': [],
    'OTHER': []
}

# Keywords for categorization
category_keywords = {
    'LEGISLATION': ['children act', 'regulations 20', 'statutory', 'legislation', 'practice direction', 'family procedure rules'],
    'CAFCASS_REPORTS': ['cafcass', 'children and family court advisory', 'guardian', 'section 7 report', 'rule 16'],
    'SOCIAL_WORK': ['social worker', 'social work', 'local authority', 'cambridgeshire county council', 'ccc', 'assessment', 'care plan'],
    'MEDICAL': ['medical', 'hospital', 'gp ', 'doctor', 'health visitor', 'nhs', 'diagnosis', 'prescription'],
    'POLICE': ['police', 'constabulary', 'officer', 'crime', 'investigation', 'arrest', 'bail', 'custody', 'operation scan'],
    'COURT_ORDERS': ['order', 'ordered', 'judgment', 'recital', 'upon hearing', 'it is ordered'],
    'EXPERT_REPORTS': ['expert', 'psycholog', 'psychiatr', 'assessment report', 'dr ', 'professor'],
    'CORRESPONDENCE': ['email', 'dear ', 'regards', 'sincerely', 'letter', '@'],
    'SCHOOL_RECORDS': ['school', 'teacher', 'education', 'ofsted', 'sen ', 'ehcp'],
    'WITNESS_STATEMENTS': ['witness statement', 'i make this statement', 'statement of', 'i am the'],
    'POSITION_STATEMENTS': ['position statement', 'submissions', 'on behalf of'],
    'SKELETON_ARGUMENTS': ['skeleton argument', 'legal argument', 'submissions of law'],
    'BUNDLES_INDEX': ['index', 'bundle', 'section a', 'section b', 'contents']
}

# Process each document
doc_updates = []
stats = defaultdict(int)

for doc_id, filename, title, doc_category, text_preview, file_type, current_case in documents:
    text_to_analyze = ((filename or '') + ' ' + (title or '') + ' ' + (text_preview or '')).lower()
    
    # Determine category
    assigned_category = None
    for cat, keywords in category_keywords.items():
        for kw in keywords:
            if kw in text_to_analyze:
                assigned_category = cat
                break
        if assigned_category:
            break
    
    if not assigned_category:
        assigned_category = 'OTHER'
    
    categories[assigned_category].append({
        'id': doc_id,
        'filename': filename,
        'title': title,
        'current_category': doc_category,
        'current_case': current_case
    })
    stats[assigned_category] += 1

print("\nDocument Distribution by Category:")
print("-"*50)
for cat, count in sorted(stats.items(), key=lambda x: -x[1]):
    print(f"  {cat:25} : {count:4} documents")

# Now let's try to assign unassigned docs to the main case
# and update their categories

print("\n" + "="*70)
print("SAMPLE DOCUMENTS BY CATEGORY")
print("="*70)

for cat, docs in categories.items():
    if docs:
        print(f"\n{cat} ({len(docs)} documents):")
        for doc in docs[:3]:  # Show first 3
            print(f"  - {doc['filename'] or doc['title']}")
            print(f"    Current category: {doc['current_category']}")

# Update document categories where they're currently 'other' or None
print("\n" + "="*70)
print("UPDATING DOCUMENT CATEGORIES")
print("="*70)

category_map = {
    'LEGISLATION': 'legislation',
    'CAFCASS_REPORTS': 'cafcass_report',
    'SOCIAL_WORK': 'social_work_report',
    'MEDICAL': 'medical_records',
    'POLICE': 'police_report',
    'COURT_ORDERS': 'court_order',
    'EXPERT_REPORTS': 'expert_report',
    'CORRESPONDENCE': 'email_correspondence',
    'SCHOOL_RECORDS': 'school_records',
    'WITNESS_STATEMENTS': 'witness_statement',
    'POSITION_STATEMENTS': 'position_statement',
    'SKELETON_ARGUMENTS': 'skeleton_argument',
    'BUNDLES_INDEX': 'bundle_index',
    'OTHER': 'other'
}

update_count = 0
for cat, docs in categories.items():
    new_category = category_map.get(cat, 'other')
    for doc in docs:
        # Only update if current category is 'other' or None
        if doc['current_category'] in [None, 'other', 'OTHER']:
            cursor.execute("""
                UPDATE documents 
                SET document_category = ?
                WHERE id = ? AND (document_category IS NULL OR document_category = 'other')
            """, (new_category, doc['id']))
            if cursor.rowcount > 0:
                update_count += 1

conn.commit()
print(f"Updated {update_count} document categories")

# Now handle documents that still don't have a specific case reference
# Assign them to the main case (PE23C50095) as they're part of the overall matter
print("\n" + "="*70)
print("ASSIGNING REMAINING DOCUMENTS TO MAIN CASE")
print("="*70)

# Get documents that don't have any case assignment
cursor.execute("""
    SELECT COUNT(*) FROM documents WHERE case_id IS NULL
""")
null_case = cursor.fetchone()[0]
print(f"Documents with no case_id: {null_case}")

if null_case > 0:
    cursor.execute("""
        UPDATE documents SET case_id = ? WHERE case_id IS NULL
    """, (main_case_uuid,))
    print(f"Assigned {cursor.rowcount} documents to main case PE23C50095")

conn.commit()

# Final summary
print("\n" + "="*70)
print("FINAL DOCUMENT DISTRIBUTION")
print("="*70)

cursor.execute("""
    SELECT c.reference, COUNT(d.id) as doc_count
    FROM documents d
    JOIN cases c ON d.case_id = c.id
    GROUP BY c.reference
    ORDER BY doc_count DESC
""")

for row in cursor.fetchall():
    print(f"  {row[0]:20} : {row[1]:4} documents")

# Category distribution
print("\n" + "="*70)
print("DOCUMENT CATEGORIES")
print("="*70)

cursor.execute("""
    SELECT document_category, COUNT(*) as count
    FROM documents
    GROUP BY document_category
    ORDER BY count DESC
""")

for row in cursor.fetchall():
    print(f"  {row[0] or 'UNCATEGORIZED':30} : {row[1]:4}")

conn.close()

print("\n" + "="*70)
print("CATEGORIZATION COMPLETE")
print("="*70)

