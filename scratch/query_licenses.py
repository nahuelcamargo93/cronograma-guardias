import sqlite3
conn = sqlite3.connect('cronograma_inteligente.db')
q = """
SELECT l.nombre, l.fecha_inicio, l.fecha_fin
FROM licencias l
JOIN personal p ON l.nombre = p.nombre
WHERE p.servicio_id = 2
  AND l.fecha_fin >= '2026-08-01'
  AND l.fecha_inicio <= '2026-08-31'
"""
rows = conn.execute(q).fetchall()
for r in rows:
    print(r)
conn.close()
