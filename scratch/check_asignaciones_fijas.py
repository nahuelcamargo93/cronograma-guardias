import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

print("=== Asignaciones Fijas activas ===")
cursor.execute("""
    SELECT personal_nombre, codigo_regla, parametros_json 
    FROM personal_reglas pr
    WHERE pr.codigo_regla = 'ASIGNACION_FIJA' AND pr.activo = 1
""")
rows = cursor.fetchall()
for r in rows:
    print(f"Médico: {r[0]} | Params: {r[2]}")

print("\n=== Ajustes de Reglas Personales (para Julio 2026) ===")
cursor.execute("""
    SELECT personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json 
    FROM personal_reglas_ajustes 
    WHERE fecha_inicio <= '2026-07-31' AND fecha_fin >= '2026-07-01' AND activo = 1
""")
rows = cursor.fetchall()
for r in rows:
    print(r)

conn.close()
