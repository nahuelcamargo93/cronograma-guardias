import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
c = conn.cursor()

c.execute("""
    SELECT nombre, tipo, fecha_inicio, fecha_fin 
    FROM licencias 
    WHERE COALESCE(activa, 1) = 1
      AND (fecha_inicio <= '2026-08-31' AND fecha_fin >= '2026-08-01')
      AND nombre IN (SELECT nombre FROM personal WHERE servicio_id = 2)
""")
rows = c.fetchall()
print(f"Licencias activas en Agosto para el personal del Servicio 2 ({len(rows)}):")
for r in rows:
    print(r)

conn.close()
