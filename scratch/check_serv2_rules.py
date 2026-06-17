import sqlite3

db_path = "cronograma_inteligente.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=== REGLAS DEL SERVICIO 2 EN servicios_reglas ===")
cursor.execute("SELECT * FROM servicios_reglas WHERE servicio_id = 2")
for r in cursor.fetchall():
    print(r)

conn.close()
