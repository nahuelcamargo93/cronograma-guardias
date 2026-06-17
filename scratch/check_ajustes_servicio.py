import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

print("=== Ajustes temporales de Reglas de Servicio en Julio 2026 ===")
cursor.execute("""
    SELECT codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json 
    FROM servicios_reglas_ajustes 
    WHERE servicio_id = 3 AND fecha_inicio <= '2026-07-31' AND fecha_fin >= '2026-07-01' AND activo = 1
""")
for r in cursor.fetchall():
    print(r)

conn.close()
