import sqlite3
conn = sqlite3.connect('cronograma_inteligente.db')
q = """
SELECT ff.personal_nombre, ff.fecha_inicio, ff.fecha_fin
FROM personal_francos_forzados ff
JOIN personal p ON ff.personal_nombre = p.nombre
WHERE p.servicio_id = 2
  AND ff.activo = 1
"""
rows = conn.execute(q).fetchall()
for r in rows:
    print(r)
conn.close()
