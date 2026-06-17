import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

cursor.execute("SELECT nombre, categoria, rol, activo FROM personal WHERE servicio_id = 3")
rows = cursor.fetchall()
print(f"Total médicos en base de datos: {len(rows)}")
for r in rows:
    print(r)

conn.close()
