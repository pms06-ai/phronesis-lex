"""Fix case_id linkage so all data is under the correct UUID."""
import sqlite3

conn = sqlite3.connect('Phronesis/data/db/phronesis.db')
cursor = conn.cursor()

# The correct UUID for PE23C50095
correct_uuid = '815e9a07b595417784ef15dd4d3e6b4c'

# Update documents
cursor.execute("UPDATE documents SET case_id = ? WHERE case_id = 'PE23C50095'", (correct_uuid,))
docs_updated = cursor.rowcount
print(f"Updated {docs_updated} documents")

# Update claims
cursor.execute("UPDATE claims SET case_id = ? WHERE case_id = 'PE23C50095'", (correct_uuid,))
claims_updated = cursor.rowcount
print(f"Updated {claims_updated} claims")

# Update entities
cursor.execute("UPDATE entities SET case_id = ? WHERE case_id = 'PE23C50095'", (correct_uuid,))
entities_updated = cursor.rowcount
print(f"Updated {entities_updated} entities")

conn.commit()
conn.close()

print("\nCase linkage fixed - all data now under PE23C50095 (UUID: 815e9a07...)")

