"""Quick script to check database state."""
import sqlite3
import os

# Check both databases
for db_name, db_path in [
    ('Main DB', 'data/db/phronesis.db'),
    ('Phronesis DB', 'Phronesis/data/db/phronesis.db')
]:
    print(f'\n=== {db_name} ({db_path}) ===')
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get table list
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [t[0] for t in cursor.fetchall()]
        print(f'Tables: {len(tables)} total')
        
        # Count rows in key tables
        key_tables = ['cases', 'documents', 'claims', 'bias_indicators', 
                      'professionals', 'timeline_events', 'analysis_document',
                      'analysis_case', 'analysis_claim']
        for table in key_tables:
            if table in tables:
                try:
                    cursor.execute(f'SELECT COUNT(*) FROM {table}')
                    count = cursor.fetchone()[0]
                    if count > 0:
                        print(f'  {table}: {count} rows')
                except Exception as e:
                    pass
        
        # Check for case data
        for case_table in ['cases', 'analysis_case']:
            if case_table in tables:
                try:
                    cursor.execute(f"SELECT * FROM {case_table} LIMIT 3")
                    cases = cursor.fetchall()
                    if cases:
                        cursor.execute(f"PRAGMA table_info({case_table})")
                        cols = [c[1] for c in cursor.fetchall()]
                        print(f'\n  {case_table} columns: {cols[:5]}...')
                        print(f'  Sample data: {cases[0][:3]}...')
                except:
                    pass
        
        conn.close()
    else:
        print('  Not found')

