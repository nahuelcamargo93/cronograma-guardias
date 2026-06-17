import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

cursor.execute("""
    SELECT id, personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json
    FROM personal_reglas_ajustes
    WHERE codigo_regla = 'SOLO_ASIGNACIONES_FIJAS' AND activo = 1
""")

print("=== AJUSTES DE SOLO_ASIGNACIONES_FIJAS ===")
for r in cursor.fetchall():
    print(r)

cursor.execute("""
    SELECT personal_nombre, codigo_regla, activo, parametros_json
    FROM personal_reglas
    WHERE codigo_regla = 'SOLO_ASIGNACIONES_FIJAS' AND activo = 1
""")
print("\n=== REGLAS FIJAS DE SOLO_ASIGNACIONES_FIJAS ===")
for r in cursor.fetchall():
    print(r)

conn.close()
