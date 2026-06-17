import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

cursor.execute("SELECT nombre, rol, categoria, servicio_id FROM personal WHERE servicio_id = 3")
rows = cursor.fetchall()
print("=== REGISTROS DE SERVICIO 3 ===")
for r in rows:
    print(r)

conn.close()
