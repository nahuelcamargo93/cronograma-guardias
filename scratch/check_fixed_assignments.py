import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

print("--- Asignaciones fijas activas para servicio 3 ---")
cursor.execute("""
    SELECT personal_nombre, codigo_regla, parametros_json 
    FROM personal_reglas 
    WHERE codigo_regla = 'ASIGNACION_FIJA' AND activo = 1 
      AND personal_nombre IN (SELECT nombre FROM personal WHERE servicio_id = 3)
""")
for r in cursor.fetchall():
    print(r)

print("\n--- Ajustes de reglas personales para servicio 3 en julio 2026 ---")
cursor.execute("""
    SELECT personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json 
    FROM personal_reglas_ajustes 
    WHERE activo = 1 AND personal_nombre IN (SELECT nombre FROM personal WHERE servicio_id = 3)
""")
for r in cursor.fetchall():
    print(r)

conn.close()
