import sqlite3

conn = sqlite3.connect("cronograma_inteligente.db")
cursor = conn.cursor()

cursor.execute("""
    SELECT g.cronograma_id, g.nombre, g.fecha, g.turno, g.horas, p.servicio_id
    FROM guardias g
    JOIN personal p ON g.nombre = p.nombre
    WHERE g.fecha = '2026-06-30' AND p.servicio_id = 2
    ORDER BY g.cronograma_id, g.turno
""")
print("Guardias del servicio 2 el 2026-06-30:")
rows = cursor.fetchall()
for r in rows:
    print(r)
print(f"Total: {len(rows)}")

conn.close()
