#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('Phronesis/data/db/phronesis.db')
cursor = conn.cursor()

# Check how many claims have authors
cursor.execute("SELECT COUNT(*) FROM claims WHERE asserted_by IS NOT NULL AND asserted_by != ''")
with_author = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM claims")
total = cursor.fetchone()[0]

print(f"Claims with author: {with_author} / {total}")

# Show top authors
cursor.execute("""
    SELECT asserted_by, COUNT(*) as cnt 
    FROM claims 
    WHERE asserted_by IS NOT NULL AND asserted_by != '' 
    GROUP BY asserted_by 
    ORDER BY cnt DESC 
    LIMIT 20
""")
print("\nTop authors:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]} claims")

# Check if there's author info in context or claim_text we could extract
cursor.execute("""
    SELECT claim_text FROM claims 
    WHERE claim_text LIKE '%said%' OR claim_text LIKE '%stated%' OR claim_text LIKE '%reported%'
    LIMIT 10
""")
print("\nSample claims with potential author info:")
for row in cursor.fetchall():
    print(f"  {row[0][:100]}...")

conn.close()

