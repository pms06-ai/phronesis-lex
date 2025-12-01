"""
Ingest the murder investigation documents into the FCIP database.
This provides critical context for the family court case PE23C50095.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import sqlite3
from datetime import datetime
from uuid import uuid4
from pathlib import Path

# Read the extracted text
doc_path = Path('data/extracted_doc_2025-11-30.txt')
with open(doc_path, 'r', encoding='utf-8') as f:
    full_text = f.read()

# Connect to the Phronesis database
db_path = Path('Phronesis/data/db/phronesis.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create document entry - using actual schema columns with all required fields
doc_id = str(uuid4())
now = datetime.now().isoformat()

# Get file size
pdf_file_path = Path('Document_2025-11-30_225038.pdf')
file_size = pdf_file_path.stat().st_size if pdf_file_path.exists() else len(full_text.encode('utf-8'))

cursor.execute("""
    INSERT INTO documents (
        id, case_id, filename, file_type, file_size,
        raw_text, word_count, page_count, 
        is_indexed, created_at, modified_at,
        title, document_category, document_date
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    doc_id,
    'PE23C50095',  # Link to main case
    'Document_2025-11-30_225038.pdf',
    'pdf',
    file_size,
    full_text,
    len(full_text.split()),
    33,  # 33 pages
    0,  # is_indexed = False
    now,
    now,
    'Operation Scan - Murder Investigation Documents',
    'POLICE_DISCLOSURE',
    '2023-03-29',  # Date of murders
))

print(f"Added document: {doc_id}")

# Extract key claims from the murder investigation
claims = [
    # The murders
    {
        'text': 'Joshua and Gary Dunmore were murdered in their respective homes on the evening of 29th March 2023',
        'source': 'Police Bail Extension Application',
        'date': '2023-03-29',
        'author': 'DC ATKINSON',
        'category': 'FACTUAL_STATEMENT',
        'modality': 'asserted',
        'certainty': 0.99
    },
    {
        'text': 'Stephen Alderton killed Joshua Dunmore first at 19 Meridian Close Bluntisham, then drove 6 miles to 140a The Row, Sutton to kill Gary Dunmore',
        'source': 'Police Bail Extension Application',
        'date': '2023-03-29',
        'author': 'DC ATKINSON',
        'category': 'FACTUAL_STATEMENT',
        'modality': 'asserted',
        'certainty': 0.99
    },
    {
        'text': 'Stephen Alderton has pleaded guilty to both murders and is currently serving a life sentence with a minimum tariff of 30 years',
        'source': 'Police Bail Extension Application',
        'date': '2024-02-27',
        'author': 'DC ATKINSON',
        'category': 'LEGAL_OUTCOME',
        'modality': 'asserted',
        'certainty': 1.0
    },
    # The premeditation evidence
    {
        'text': 'During sentencing the Judge remarked that there was evidence of significant premeditation and planning',
        'source': 'Police Bail Extension Application',
        'date': '2024-02-27',
        'author': 'DC ATKINSON',
        'category': 'JUDICIAL_FINDING',
        'modality': 'reported',
        'certainty': 0.99
    },
    {
        'text': 'Text messages sent to Samantha as far back as April/June 2022 where Alderton referred to "Fleeing to Panama", "There is always a Plan B", and "Independence Day"',
        'source': 'Police Bail Extension Application',
        'date': '2024-02-27',
        'author': 'DC ATKINSON',
        'category': 'EVIDENCE',
        'modality': 'asserted',
        'certainty': 0.95
    },
    # The family court connection
    {
        'text': 'The DP\'s wife and Joshua Dunmore were going through a family Court case to decide on where their 7 year old son was to live',
        'source': 'Police Bail Extension Application',
        'date': '2024-02-27',
        'author': 'DC ATKINSON',
        'category': 'FACTUAL_STATEMENT',
        'modality': 'asserted',
        'certainty': 0.99
    },
    {
        'text': 'Joshua Dunmore did not want his son moving to the USA, hence the Family Court matter',
        'source': 'Police Bail Extension Application',
        'date': '2024-02-27',
        'author': 'DC ATKINSON',
        'category': 'FACTUAL_STATEMENT',
        'modality': 'asserted',
        'certainty': 0.95
    },
    {
        'text': 'On Monday 27th March 2023 there was a planned Interim Family Court hearing, in which a CAFCASS report recommended that the child was NOT to be removed from the UK whilst proceedings were in place',
        'source': 'Police Bail Extension Application',
        'date': '2024-02-27',
        'author': 'DC ATKINSON',
        'category': 'LEGAL_OUTCOME',
        'modality': 'reported',
        'certainty': 0.99
    },
    {
        'text': 'Evidence gathered thus far indicates that the DP and his wife planned to take the child to the US in March 2023 regardless of any Court adjudication',
        'source': 'Police Bail Extension Application',
        'date': '2024-02-27',
        'author': 'DC ATKINSON',
        'category': 'POLICE_ASSESSMENT',
        'modality': 'alleged',
        'certainty': 0.85
    },
    # The motive
    {
        'text': 'The motive for these offences is known to be centred around the matters heard in the family court',
        'source': 'Police Bail Extension Application',
        'date': '2024-02-27',
        'author': 'DC ATKINSON',
        'category': 'POLICE_ASSESSMENT',
        'modality': 'asserted',
        'certainty': 0.95
    },
    # Suspect status
    {
        'text': 'Your suspect status has been reinstated. The Beds, Cambs and Herts Major Crime Unit continue to investigate your suspected involvement in the offence for which you were originally arrested namely, Conspiracy to Murder',
        'source': 'DCI Katie Dounias Letter',
        'date': '2023-05-12',
        'author': 'DCI Katie DOUNIAS',
        'category': 'POLICE_DECISION',
        'modality': 'asserted',
        'certainty': 1.0
    },
    # The arrests
    {
        'text': 'Paul and Samantha Stephen were arrested at a hotel at around 00:35 hrs 30th March 2023, just over 3 hours after the first murder, on suspicion of conspiracy to murder',
        'source': 'Police Bail Extension Application',
        'date': '2024-02-27',
        'author': 'DC ATKINSON',
        'category': 'FACTUAL_STATEMENT',
        'modality': 'asserted',
        'certainty': 0.99
    },
    {
        'text': 'Paul Stephen is a serving American Airman based at RAF Mildenhall',
        'source': 'Police Bail Extension Application',
        'date': '2024-02-27',
        'author': 'DC ATKINSON',
        'category': 'FACTUAL_STATEMENT',
        'modality': 'asserted',
        'certainty': 1.0
    },
    {
        'text': 'The DP had received a posting order to return to the USA, the date of the posting meant that the DP had to be in the USA in April 2023',
        'source': 'Police Bail Extension Application',
        'date': '2024-02-27',
        'author': 'DC ATKINSON',
        'category': 'FACTUAL_STATEMENT',
        'modality': 'asserted',
        'certainty': 0.99
    },
    # Investigation scope
    {
        'text': 'Police are considering and investigating offences of Conspiring to Abduct a Child and Perverting the Course of Justice',
        'source': 'Police Bail Extension Application',
        'date': '2024-02-27',
        'author': 'DC ATKINSON',
        'category': 'POLICE_DECISION',
        'modality': 'asserted',
        'certainty': 0.99
    },
    # Final outcome
    {
        'text': 'No further action will be taken in respect of Conspiracy to Murder, Perverting the Course of Justice, Attempting Abduction, Possession of Firearm - There is insufficient evidence to provide a realistic prospect of conviction',
        'source': 'MG4F NFA Notification',
        'date': '2025-02-12',
        'author': 'DC 2072 ATKINSON',
        'category': 'POLICE_DECISION',
        'modality': 'asserted',
        'certainty': 1.0
    },
    # The child Ryan
    {
        'text': 'Paul and Samantha Stephen have been arrested on suspicion of conspiring to murder 8 year old Ryan\'s father and paternal grandfather',
        'source': 'Police Bail Extension Application',
        'date': '2024-02-27',
        'author': 'DC ATKINSON',
        'category': 'FACTUAL_STATEMENT',
        'modality': 'asserted',
        'certainty': 0.99
    },
    {
        'text': 'Joshua Dunmore is Samantha\'s ex-partner, with whom she has a 7 year old boy who is diagnosed with autism',
        'source': 'Police Bail Extension Application',
        'date': '2024-02-27',
        'author': 'DC ATKINSON',
        'category': 'FACTUAL_STATEMENT',
        'modality': 'asserted',
        'certainty': 0.99
    },
]

# Insert claims - using actual schema columns
claim_count = 0
for claim in claims:
    claim_id = str(uuid4())
    cursor.execute("""
        INSERT INTO claims (
            id, document_id, case_id, claim_text, context,
            date_made, asserted_by, claim_type,
            modality, certainty, ai_extracted, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        claim_id,
        doc_id,
        'PE23C50095',
        claim['text'],
        claim['source'],  # Using context for source
        claim['date'],
        claim['author'],
        claim['category'],
        claim['modality'],
        claim['certainty'],
        0,  # Not AI extracted
        datetime.now().isoformat()
    ))
    claim_count += 1

print(f"Added {claim_count} claims from murder investigation")

# Add key entities - using actual schema columns
entities = [
    ('Stephen Alderton', 'PERSON', 'PERPETRATOR', 'Samantha Stephen\'s father, convicted of double murder'),
    ('Joshua Dunmore', 'PERSON', 'VICTIM', 'Ryan\'s biological father (never married to Samantha) - murdered 29/03/2023'),
    ('Gary Dunmore', 'PERSON', 'VICTIM', 'Joshua\'s father, Ryan\'s paternal grandfather - murdered 29/03/2023'),
    ('DCI Katie Dounias', 'PROFESSIONAL', 'POLICE_SIO', 'Senior Investigating Officer, Beds Cambs Herts Major Crime Unit'),
    ('DC 2072 Atkinson', 'PROFESSIONAL', 'POLICE_OIC', 'Officer in Case, Cambridgeshire Constabulary'),
    ('Ryan', 'CHILD', 'SUBJECT_CHILD', '7 year old (as of 2023) autistic son of Samantha and Joshua Dunmore'),
]

entity_count = 0
for name, entity_type, role, notes in entities:
    entity_id = str(uuid4())
    try:
        cursor.execute("""
            INSERT INTO entities (
                id, entity_id, case_id, name, entity_type, role, notes, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entity_id,
            entity_id,  # entity_id same as id
            'PE23C50095',
            name,
            entity_type,
            role,
            notes,
            datetime.now().isoformat()
        ))
        entity_count += 1
    except sqlite3.IntegrityError:
        # Entity might already exist
        pass

print(f"Added {entity_count} new entities")

# Commit changes
conn.commit()
conn.close()

print("\n" + "="*60)
print("MURDER INVESTIGATION DATA INGESTED")
print("="*60)
print(f"""
This document establishes the CRITICAL context for case PE23C50095:

1. MURDERS: Ryan's biological father (Joshua) and grandfather (Gary) 
   were shot dead by Samantha's father (Stephen Alderton) on 29/03/2023

2. MOTIVE: The family court custody dispute over Ryan - they wanted 
   to take him to USA despite CAFCASS recommending against it

3. SUSPECTS: Paul and Samantha Stephen were investigated for 
   Conspiracy to Murder for almost 2 years (March 2023 - Feb 2025)

4. PREMEDITATION: Judge found "significant premeditation" with 
   texts about "Panama", "Plan B", and "Independence Day"

5. OUTCOME: NFA (No Further Action) in Feb 2025 due to 
   "insufficient evidence for realistic prospect of conviction"

This context is ESSENTIAL for understanding:
- Why professionals may have had suspicions about Paul/Samantha
- Why Ryan's placement was so contested
- Why certain allegations were made in family proceedings
- The extreme circumstances this family court case exists within
""")

