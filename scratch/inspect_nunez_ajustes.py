import sqlite3

db_path = "cronograma_inteligente.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("""
    SELECT * 
    FROM personal_reglas_ajustes
    WHERE personal_nombre LIKE '%N%ez%'
""")
print("Adjustments for Nuñez:")
for row in cur.fetchall():
    print(row)

conn.close()
