import sqlite3

db_path = "cronograma_inteligente.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("SELECT nombre, activo FROM personal WHERE nombre LIKE '%Florencia%' OR nombre LIKE '%N%'")
print("Matching personal rows:")
for row in cur.fetchall():
    if 'Florencia' in row[0] or 'ez' in row[0]:
        print(row)

conn.close()
