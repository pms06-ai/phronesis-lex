"""Find all case numbers referenced in the documents."""
import sqlite3
import re
from collections import Counter

conn = sqlite3.connect('Phronesis/data/db/phronesis.db')
cursor = conn.cursor()

# Get all document text
cursor.execute("SELECT id, title, filename, raw_text FROM documents WHERE raw_text IS NOT NULL")
documents = cursor.fetchall()

print("="*70)
print("SEARCHING FOR CASE NUMBERS IN 566 DOCUMENTS")
print("="*70)

# Common UK family court case number patterns
patterns = [
    # Family court patterns: PE23C50095, ZC21P00123, etc.
    r'\b[A-Z]{2}\d{2}[A-Z]\d{5}\b',
    # Alternative patterns: PE23C 50095
    r'\b[A-Z]{2}\d{2}[A-Z]\s?\d{5}\b',
    # Court reference patterns like 2023/1234
    r'\b20\d{2}/\d{4,6}\b',
    # Appeal court: CA-2024-001234
    r'\bCA[-\s]?\d{4}[-\s]?\d{4,6}\b',
    # High court: [2024] EWHC 1234
    r'\[\d{4}\]\s*[A-Z]{2,4}\s*\d+',
    # Police URN: 35/KL/392/23
    r'\b\d{2}/[A-Z]{2}/\d{3,4}/\d{2}\b',
    # Generic case refs
    r'\bCase\s*(?:No\.?|Number|Ref\.?)[:\s]*([A-Z0-9\-/]+)',
]

all_case_refs = Counter()
case_ref_contexts = {}

for doc_id, title, filename, raw_text in documents:
    if not raw_text:
        continue
    
    for pattern in patterns:
        matches = re.findall(pattern, raw_text, re.IGNORECASE)
        for match in matches:
            # Clean up the match
            if isinstance(match, tuple):
                match = match[0]
            match = match.strip().upper()
            
            # Skip very short or common false positives
            if len(match) < 6:
                continue
            if match in ['2023/2024', '2022/2023', '2021/2022']:
                continue
                
            all_case_refs[match] += 1
            
            # Store context (first occurrence)
            if match not in case_ref_contexts:
                # Find context around the match
                idx = raw_text.upper().find(match)
                if idx >= 0:
                    start = max(0, idx - 50)
                    end = min(len(raw_text), idx + len(match) + 50)
                    context = raw_text[start:end].replace('\n', ' ')
                    case_ref_contexts[match] = {
                        'context': context,
                        'filename': filename,
                        'title': title
                    }

print(f"\nFound {len(all_case_refs)} unique case references\n")

# Sort by frequency
print("="*70)
print("CASE REFERENCES BY FREQUENCY")
print("="*70)

for ref, count in all_case_refs.most_common(30):
    print(f"\n{ref}: {count} occurrences")
    if ref in case_ref_contexts:
        ctx = case_ref_contexts[ref]
        print(f"  First seen in: {ctx['filename'] or ctx['title']}")
        print(f"  Context: ...{ctx['context']}...")

# Also search for specific mentions of "case number" or "reference"
print("\n" + "="*70)
print("SEARCHING FOR EXPLICIT CASE NUMBER MENTIONS")
print("="*70)

cursor.execute("""
    SELECT DISTINCT claim_text 
    FROM claims 
    WHERE claim_text LIKE '%case number%' 
    OR claim_text LIKE '%case ref%'
    OR claim_text LIKE '%proceedings%number%'
    LIMIT 20
""")

for row in cursor.fetchall():
    print(f"\n- {row[0][:200]}...")

# Search for court orders which typically have case numbers in headers
print("\n" + "="*70)
print("COURT ORDER DOCUMENTS (likely contain case numbers)")
print("="*70)

cursor.execute("""
    SELECT filename, title, SUBSTR(raw_text, 1, 500) as header
    FROM documents 
    WHERE document_category = 'court_order'
    LIMIT 10
""")

for row in cursor.fetchall():
    print(f"\n{row[0] or row[1]}:")
    # Extract any case numbers from header
    header = row[2] or ""
    for pattern in patterns:
        matches = re.findall(pattern, header, re.IGNORECASE)
        if matches:
            print(f"  Case refs found: {matches}")

conn.close()

