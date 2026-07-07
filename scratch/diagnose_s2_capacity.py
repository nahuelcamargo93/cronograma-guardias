import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
c = conn.cursor()

# Find a week where an employee worked TNN
c.execute("""
    SELECT g.nombre, g.fecha, g.turno, sc.categoria, sc.fecha_lunes
    FROM guardias g
    JOIN semanas_categorias sc ON g.cronograma_id = sc.cronograma_id AND g.nombre = sc.nombre
    WHERE g.cronograma_id = 610 AND g.turno = 'TNN'
      AND g.fecha BETWEEN sc.fecha_lunes AND date(sc.fecha_lunes, '+6 days')
    LIMIT 10
""")
rows = c.fetchall()
print("TNN shifts and their stored week category in 610:")
for r in rows:
    print(r)

conn.close()
