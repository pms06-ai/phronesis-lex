#!/usr/bin/env python3
"""
Fix relationship data to correct the assumption that Samantha and Joshua were married.
They were never married - they share a child (Ryan) but were co-parents only.
"""

import sqlite3

db_path = 'Phronesis/data/db/phronesis.db'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check current entity notes
print("Current entity notes:")
cursor.execute("SELECT name, notes FROM entities WHERE name LIKE '%Joshua%' OR name LIKE '%Samantha%'")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]}")

# Update Joshua's notes to clarify relationship
cursor.execute("""
    UPDATE entities 
    SET notes = "Ryan's biological father (never married to Samantha) - murdered 29/03/2023"
    WHERE name LIKE '%Joshua%'
""")
updated = cursor.rowcount
print(f"\nUpdated {updated} Joshua entity notes")

# Update any notes that incorrectly say "ex-partner" or imply marriage
cursor.execute("""
    UPDATE entities 
    SET notes = REPLACE(notes, 'ex-partner', 'co-parent (never married)')
    WHERE notes LIKE '%ex-partner%'
""")
updated = cursor.rowcount
print(f"Updated {updated} 'ex-partner' references")

conn.commit()

# Verify changes
print("\nUpdated entity notes:")
cursor.execute("SELECT name, notes FROM entities WHERE name LIKE '%Joshua%' OR name LIKE '%Samantha%'")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]}")

conn.close()
print("\n✅ Relationship data corrected")

