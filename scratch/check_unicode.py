import sqlite3

conn = sqlite3.connect("cronograma_inteligente.db")
cursor = conn.cursor()

cursor.execute("SELECT nombre FROM personal WHERE nombre LIKE 'GUI%'")
row = cursor.fetchone()
if row:
    name = row[0]
    print(f"Name: {name}")
    print("Codes:", [ord(c) for c in name])

conn.close()
