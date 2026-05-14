import sqlite3
import pandas as pd

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

# Get tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [t[0] for t in cursor.fetchall()]
print("Tables:", tables)

# Search for personnel and licenses
for table in tables:
    if 'personal' in table.lower() or 'licencia' in table.lower() or 'servicio' in table.lower():
        print(f"\n--- {table} ---")
        try:
            df = pd.read_sql_query(f"SELECT * FROM {table} LIMIT 5", conn)
            print(df)
        except Exception as e:
            print(f"Error reading {table}: {e}")

conn.close()
