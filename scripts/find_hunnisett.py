import sqlite3
conn = sqlite3.connect('Phronesis/data/db/phronesis.db')
cursor = conn.cursor()
cursor.execute("""
    SELECT filename, document_category, title 
    FROM documents 
    WHERE LOWER(filename) LIKE '%hunnisett%' 
    OR LOWER(title) LIKE '%hunnisett%'
    OR LOWER(raw_text) LIKE '%dr hunnisett%'
    OR LOWER(raw_text) LIKE '%dr. hunnisett%'
""")
print("Dr Hunnisett documents found:")
for row in cursor.fetchall():
    print(f"  {row[0]} ({row[1]})")
conn.close()

