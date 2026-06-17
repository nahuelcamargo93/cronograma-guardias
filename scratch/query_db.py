import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

print("--- BUSCANDO REGLA SEMANAS_SEGUIMIENTO_REQUERIDAS EN PERSONAL_REGLAS ---")
rows_pr = cursor.execute("""
SELECT personal_nombre, activo, parametros_json
FROM personal_reglas
WHERE codigo_regla = 'SEMANAS_SEGUIMIENTO_REQUERIDAS'
""").fetchall()
for r in rows_pr:
    print(f"Empleado: {r[0]}, Activo: {r[1]}, Params: {r[2]}")

print("\n--- BUSCANDO REGLA SEMANAS_SEGUIMIENTO_REQUERIDAS EN AJUSTES DE PERSONAL ---")
rows_pra = cursor.execute("""
SELECT personal_nombre, activo, accion, fecha_inicio, fecha_fin, parametros_json
FROM personal_reglas_ajustes
WHERE codigo_regla = 'SEMANAS_SEGUIMIENTO_REQUERIDAS'
""").fetchall()
for r in rows_pra:
    print(f"Empleado: {r[0]}, Activo: {r[1]}, Accion: {r[2]}, Rango: {r[3]} a {r[4]}, Params: {r[5]}")

conn.close()
