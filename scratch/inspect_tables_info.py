import sqlite3

db_path = "cronograma_inteligente.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

for table in ['servicios_reglas', 'personal_reglas', 'personal', 'guardias', 'reglas_catalogo']:
    cur.execute(f"PRAGMA table_info({table})")
    print(f"Columns in {table}:")
    for row in cur.fetchall():
        print(f"  {row[1]} ({row[2]})")

conn.close()
