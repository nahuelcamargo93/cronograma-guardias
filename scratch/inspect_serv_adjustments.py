import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

print("=== AJUSTES DE REGLAS DE SERVICIO EN JULIO ===")
cursor.execute("""
    SELECT id, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json
    FROM servicios_reglas_ajustes
    WHERE servicio_id = 3 AND activo = 1
      AND ((fecha_inicio BETWEEN '2026-07-01' AND '2026-07-31') 
           OR (fecha_fin BETWEEN '2026-07-01' AND '2026-07-31')
           OR (fecha_inicio <= '2026-07-01' AND fecha_fin >= '2026-07-31'))
""")
for r in cursor.fetchall():
    print(r)

conn.close()
