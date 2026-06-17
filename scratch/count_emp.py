import sqlite3

db_path = "cronograma_inteligente.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT count(*) FROM personal WHERE servicio_id = 2 AND activo = 1")
print("Total Active Employees for Servicio 2:", cursor.fetchone()[0])

cursor.execute("SELECT nombre, rol FROM personal WHERE servicio_id = 2 AND activo = 1")
for row in cursor.fetchall():
    print(row)

conn.close()
