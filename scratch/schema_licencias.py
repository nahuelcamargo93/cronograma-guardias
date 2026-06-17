import sqlite3

conn = sqlite3.connect("cronograma_inteligente.db")
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(licencias);")
print("Esquema licencias:")
for c in cursor.fetchall():
    print(c)

conn.close()
