import sqlite3

db_path = "cronograma_inteligente.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("""
    SELECT * 
    FROM licencias
    WHERE nombre LIKE '%Graciela%'
""")
print("Licencias for Aguilera Graciela:")
for row in cur.fetchall():
    print(row)

conn.close()
