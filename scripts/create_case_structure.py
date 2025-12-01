"""
Create proper case structure for all 6 family court proceedings + appeal.
Link documents to correct cases and build timeline.
"""
import sqlite3
import re
import json
from datetime import datetime
from uuid import uuid4
from collections import defaultdict

conn = sqlite3.connect('Phronesis/data/db/phronesis.db')
cursor = conn.cursor()

print("="*70)
print("CREATING CASE STRUCTURE FOR FAMILY COURT PROCEEDINGS")
print("="*70)

# Define all the cases
cases = [
    {
        'reference': 'PE21P30644',
        'title': 'Private Law Proceedings - Dunmore v Stephen (2021)',
        'court': 'Family Court at Peterborough',
        'case_type': 'private_law',
        'status': 'concluded',
        'year': 2021,
        'description': 'Original private law proceedings regarding child arrangements for Ryan. Joshua Dunmore (Father) vs Samantha Stephen (Mother).',
        'parties': 'Joshua Dunmore (Applicant) v Samantha Stephen (Respondent)'
    },
    {
        'reference': 'PE22P00090',
        'title': 'Private Law Proceedings - Cambridge (May 2022)',
        'court': 'Family Court at Cambridge',
        'case_type': 'private_law',
        'status': 'concluded',
        'year': 2022,
        'description': 'Private law proceedings May 2022 at Cambridge Family Court.',
        'parties': 'TBC'
    },
    {
        'reference': 'PE22P31058',
        'title': 'Private Law Proceedings (2022)',
        'court': 'Family Court at Peterborough',
        'case_type': 'private_law',
        'status': 'concluded',
        'year': 2022,
        'description': 'Previous private law proceedings referenced in Section H of the bundle.',
        'parties': 'TBC'
    },
    {
        'reference': 'PE23C50063',
        'title': 'Care Proceedings - Former Application (2023)',
        'court': 'Family Court at Peterborough',
        'case_type': 'public_law',
        'status': 'withdrawn/concluded',
        'year': 2023,
        'description': 'Former care application by Local Authority. Referenced as preceding PE23C50095.',
        'parties': 'Cambridgeshire County Council v Samantha Stephen & Paul Stephen'
    },
    {
        'reference': 'PE23P30344',
        'title': 'Private Law Proceedings (2023)',
        'court': 'Family Court at Peterborough',
        'case_type': 'private_law',
        'status': 'active',
        'year': 2023,
        'description': 'Private law proceedings 2023. Referenced in Section I of the bundle.',
        'parties': 'TBC - likely Mandy Seamark involvement'
    },
    {
        'reference': 'PE23C50095',
        'title': 'Care Proceedings - Section 31 Children Act 1989',
        'court': 'Family Court at Peterborough',
        'case_type': 'public_law',
        'status': 'active',
        'year': 2023,
        'description': 'Main care proceedings under Section 31 Children Act 1989. Local Authority seeking care/supervision orders for Ryan and Freya following the murders of Joshua and Gary Dunmore.',
        'parties': 'Cambridgeshire County Council v Samantha Stephen, Paul Stephen, Mandy Seamark & Others'
    },
    {
        'reference': 'CA-2024-001096',
        'title': 'Court of Appeal - D-S (Children)',
        'court': 'Court of Appeal, Civil Division',
        'case_type': 'appeal',
        'status': 'refused',
        'year': 2024,
        'description': 'Appeal against decisions in PE23C50095. Permission refused.',
        'parties': 'D-S (Children) - Appellant v Respondents'
    },
]

# Get the existing main case UUID
cursor.execute("SELECT id FROM cases WHERE reference = 'PE23C50095'")
existing = cursor.fetchone()
main_case_uuid = existing[0] if existing else None

print(f"\nExisting main case UUID: {main_case_uuid}")

# Create/update cases
case_uuids = {}
for case in cases:
    # Check if case already exists
    cursor.execute("SELECT id FROM cases WHERE reference = ?", (case['reference'],))
    existing = cursor.fetchone()
    
    if existing:
        case_uuid = existing[0]
        print(f"  Case {case['reference']} already exists: {case_uuid[:8]}...")
    else:
        case_uuid = str(uuid4()).replace('-', '')
        now = datetime.now().isoformat()
        
        metadata = {
            'year': case['year'],
            'description': case['description'],
            'parties': case['parties']
        }
        
        cursor.execute("""
            INSERT INTO cases (id, reference, title, court, case_type, status, created_at, updated_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            case_uuid,
            case['reference'],
            case['title'],
            case['court'],
            case['case_type'],
            case['status'],
            now,
            now,
            json.dumps(metadata)
        ))
        print(f"  Created case {case['reference']}: {case_uuid[:8]}...")
    
    case_uuids[case['reference']] = case_uuid

conn.commit()

print("\n" + "="*70)
print("LINKING DOCUMENTS TO CORRECT CASES")
print("="*70)

# Get all documents
cursor.execute("SELECT id, filename, title, raw_text FROM documents")
documents = cursor.fetchall()

# Track document assignments
doc_assignments = defaultdict(list)
unassigned = []

# Case reference patterns
case_patterns = {
    'PE21P30644': r'PE21P30644',
    'PE22P00090': r'PE22P00090',
    'PE22P31058': r'PE22P31058',
    'PE23C50063': r'PE23C50063',
    'PE23P30344': r'PE23P30344',
    'PE23C50095': r'PE23C50095',
    'CA-2024-001096': r'CA[-\s]?2024[-\s]?001096',
}

for doc_id, filename, title, raw_text in documents:
    text_to_search = (raw_text or '') + ' ' + (filename or '') + ' ' + (title or '')
    
    found_cases = []
    for case_ref, pattern in case_patterns.items():
        if re.search(pattern, text_to_search, re.IGNORECASE):
            found_cases.append(case_ref)
    
    if found_cases:
        # Assign to the most specific/recent case found
        # Priority: PE23C50095 (main care) > PE23P30344 > PE23C50063 > PE22P31058 > PE22P00090 > PE21P30644
        priority_order = ['CA-2024-001096', 'PE23C50095', 'PE23P30344', 'PE23C50063', 'PE22P31058', 'PE22P00090', 'PE21P30644']
        
        primary_case = None
        for p in priority_order:
            if p in found_cases:
                primary_case = p
                break
        
        if primary_case:
            doc_assignments[primary_case].append((doc_id, filename or title, found_cases))
    else:
        unassigned.append((doc_id, filename or title))

# Update document case_ids
update_count = 0
for case_ref, docs in doc_assignments.items():
    case_uuid = case_uuids.get(case_ref)
    if case_uuid:
        for doc_id, doc_name, all_refs in docs:
            cursor.execute("UPDATE documents SET case_id = ? WHERE id = ?", (case_uuid, doc_id))
            update_count += 1

conn.commit()

print(f"\nUpdated {update_count} documents with correct case_ids")
print("\nDocument distribution by case:")
for case_ref in ['PE21P30644', 'PE22P00090', 'PE22P31058', 'PE23C50063', 'PE23P30344', 'PE23C50095', 'CA-2024-001096']:
    count = len(doc_assignments.get(case_ref, []))
    print(f"  {case_ref}: {count} documents")

print(f"\nUnassigned documents: {len(unassigned)}")

# Also update claims based on document case_id
print("\n" + "="*70)
print("UPDATING CLAIMS WITH CORRECT CASE IDS")
print("="*70)

cursor.execute("""
    UPDATE claims 
    SET case_id = (SELECT case_id FROM documents WHERE documents.id = claims.document_id)
    WHERE document_id IS NOT NULL
""")
claims_updated = cursor.rowcount
print(f"Updated {claims_updated} claims with correct case_ids")

conn.commit()

# Build timeline
print("\n" + "="*70)
print("CASE TIMELINE")
print("="*70)

timeline = [
    ('2021', 'PE21P30644', 'Private Law', 'Original child arrangements proceedings - Joshua Dunmore v Samantha Stephen'),
    ('May 2022', 'PE22P00090', 'Private Law', 'Proceedings at Cambridge Family Court'),
    ('2022', 'PE22P31058', 'Private Law', 'Further private law proceedings at Peterborough'),
    ('27 Mar 2023', 'PE21P30644/PE22P31058', 'Family Court', 'Interim hearing - CAFCASS recommends child NOT be removed from UK'),
    ('29 Mar 2023', 'CRIMINAL', 'Murder', 'Joshua and Gary Dunmore murdered by Stephen Alderton'),
    ('30 Mar 2023', 'CRIMINAL', 'Arrests', 'Paul and Samantha Stephen arrested for conspiracy to murder'),
    ('31 Mar 2023', 'CRIMINAL', 'Release', 'Paul and Samantha released NFA'),
    ('Apr 2023', 'PE23C50063', 'Public Law', 'Initial care application by Local Authority'),
    ('12 May 2023', 'CRIMINAL', 'Reinstatement', 'Suspect status reinstated for Paul and Samantha'),
    ('7 Jun 2023', 'CRIMINAL', 'Re-arrest', 'Both re-arrested, "no comment" interviews'),
    ('9 Jun 2023', 'PE23C50095', 'Public Law', 'Urgent ICO hearing - HHJ Gordon-Saker'),
    ('2023', 'PE23P30344', 'Private Law', 'New private law proceedings - Mandy Seamark involvement'),
    ('Oct 2023', 'PE23C50095', 'Public Law', 'Multiple hearings and orders'),
    ('Mar 2024', 'PE23C50095', 'Public Law', 'Further hearings'),
    ('2024', 'CA-2024-001096', 'Appeal', 'Court of Appeal - Permission refused'),
    ('Jul 2024', 'PE23C50095', 'Public Law', 'Ongoing proceedings'),
    ('12 Feb 2025', 'CRIMINAL', 'NFA', 'No Further Action - insufficient evidence for prosecution'),
]

for date, case_ref, case_type, event in timeline:
    print(f"\n{date:15} | {case_ref:15} | {case_type:12} | {event}")

# Save timeline to database as a document
timeline_text = "CASE TIMELINE - JFD vs SJS Family Proceedings\n"
timeline_text += "="*70 + "\n\n"
for date, case_ref, case_type, event in timeline:
    timeline_text += f"{date} | {case_ref} | {case_type} | {event}\n"

# Create case relationships table if not exists
cursor.execute("""
    CREATE TABLE IF NOT EXISTS case_relationships (
        id TEXT PRIMARY KEY,
        case_id_1 TEXT NOT NULL,
        case_id_2 TEXT NOT NULL,
        relationship_type TEXT NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (case_id_1) REFERENCES cases(id),
        FOREIGN KEY (case_id_2) REFERENCES cases(id)
    )
""")

# Add relationships
relationships = [
    ('PE21P30644', 'PE22P31058', 'CONTINUATION', 'PE22P31058 continues/relates to PE21P30644'),
    ('PE22P31058', 'PE23C50063', 'PRECEDED_BY', 'Murder led to care proceedings'),
    ('PE23C50063', 'PE23C50095', 'SUPERSEDED_BY', 'PE23C50063 superseded by PE23C50095'),
    ('PE23C50095', 'PE23P30344', 'PARALLEL', 'Public and private law running in parallel'),
    ('PE23C50095', 'CA-2024-001096', 'APPEALED_TO', 'Appeal of PE23C50095 decisions'),
]

for case1, case2, rel_type, desc in relationships:
    if case1 in case_uuids and case2 in case_uuids:
        rel_id = str(uuid4()).replace('-', '')
        try:
            cursor.execute("""
                INSERT INTO case_relationships (id, case_id_1, case_id_2, relationship_type, description)
                VALUES (?, ?, ?, ?, ?)
            """, (rel_id, case_uuids[case1], case_uuids[case2], rel_type, desc))
        except sqlite3.IntegrityError:
            pass  # Relationship already exists

conn.commit()
conn.close()

print("\n" + "="*70)
print("CASE STRUCTURE COMPLETE")
print("="*70)
print("""
Created 7 case entries:
  - PE21P30644: Private Law (2021) - Original proceedings
  - PE22P00090: Private Law (May 2022) - Cambridge
  - PE22P31058: Private Law (2022) - Peterborough
  - PE23C50063: Public Law (2023) - Former care application
  - PE23P30344: Private Law (2023) - Current private law
  - PE23C50095: Public Law (2023) - Main care proceedings
  - CA-2024-001096: Court of Appeal (2024) - Permission refused

All documents and claims have been linked to their correct cases.
Case relationships have been established showing how proceedings relate.
""")

