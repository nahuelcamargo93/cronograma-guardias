import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

print("=== Ajustes de Demanda en Julio 2026 ===")
cursor.execute("""
    SELECT da.fecha_inicio, da.fecha_fin, dc.puesto_id, p.nombre, da.cantidad_min, da.cantidad_max, da.dias_semana
    FROM demanda_ajustes da
    JOIN demanda_config dc ON da.demanda_config_id = dc.id
    JOIN puestos p ON dc.puesto_id = p.id
    WHERE da.activo = 1 AND da.fecha_inicio <= '2026-07-31' AND da.fecha_fin >= '2026-07-01'
""")
for r in cursor.fetchall():
    print(r)

conn.close()
