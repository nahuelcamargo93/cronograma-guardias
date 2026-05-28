import sqlite3

db_path = "cronograma_inteligente.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("PRAGMA table_info(demanda_ajustes)")
print("Columns in demanda_ajustes:")
for row in cur.fetchall():
    print(f"  {row[1]} ({row[2]})")

cur.execute("SELECT * FROM demanda_ajustes LIMIT 10")
print("\nRows in demanda_ajustes:")
for row in cur.fetchall():
    print(row)

conn.close()
