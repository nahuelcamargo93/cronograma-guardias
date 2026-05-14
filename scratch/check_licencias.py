import sqlite3
import pandas as pd

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [t[0] for t in cursor.fetchall()]
print("Tables found:", tables)

# Check for licencias table
if 'licencias' in tables:
    print("\n--- Content of 'licencias' table ---")
    df_licencias = pd.read_sql_query("""
        SELECT l.*, p.nombre as nombre_personal, s.nombre as nombre_servicio
        FROM licencias l
        JOIN personal p ON l.personal_id = p.id
        JOIN servicios s ON p.servicio_id = s.id
    """, conn)
    print(df_licencias)
    
    # Summary by service
    print("\n--- Summary of licencias by service ---")
    print(df_licencias.groupby('nombre_servicio').size())
else:
    print("\nNo 'licencias' table found.")

# Check personal table to see what services exist
if 'personal' in tables:
    print("\n--- Summary of personnel by service ---")
    df_personal = pd.read_sql_query("""
        SELECT s.nombre as nombre_servicio, count(*) as count
        FROM personal p
        JOIN servicios s ON p.servicio_id = s.id
        GROUP BY s.nombre
    """, conn)
    print(df_personal)

conn.close()
