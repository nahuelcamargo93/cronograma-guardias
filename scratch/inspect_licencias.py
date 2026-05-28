import sqlite3

db_path = "cronograma_inteligente.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("PRAGMA table_info(licencias)")
print("Columns in licencias:")
for row in cur.fetchall():
    print(f"  {row[1]} ({row[2]})")

cur.execute("SELECT * FROM licencias LIMIT 5")
print("\nRows in licencias:")
for row in cur.fetchall():
    print(row)

conn.close()
