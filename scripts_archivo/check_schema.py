import sqlite3
import pandas as pd

conn = sqlite3.connect('cronograma_inteligente.db')

# Get tables
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [t[0] for t in cursor.fetchall()]
print("Tables found:", tables)

if 'licencias' in tables:
    print("\n--- Columns in 'licencias' table ---")
    cursor.execute("PRAGMA table_info(licencias)")
    columns = cursor.fetchall()
    for col in columns:
        print(col)
        
    print("\n--- First 5 rows of 'licencias' ---")
    df_licencias = pd.read_sql_query("SELECT * FROM licencias LIMIT 5", conn)
    print(df_licencias)

conn.close()
