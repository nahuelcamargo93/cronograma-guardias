import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

print("=== SERVICE 3: ASIGNACION_FIJA IN personal_reglas ===")
cursor.execute("""
    SELECT pr.personal_nombre, rc.codigo_regla, pr.parametros_json
    FROM personal_reglas pr
    JOIN reglas_catalogo rc ON pr.regla_id = rc.id
    JOIN personal p ON pr.personal_nombre = p.nombre
    WHERE p.servicio_id = 3 AND rc.codigo_regla = 'ASIGNACION_FIJA'
""")
for r in cursor.fetchall():
    print(f"Name: {r[0]}, Rule: {r[1]}, Params: {r[2]}")

print("\n=== SERVICE 3: ASIGNACION_FIJA IN personal_reglas_ajustes ===")
cursor.execute("""
    SELECT apr.personal_nombre, apr.codigo_regla, apr.accion, apr.parametros_json, apr.fecha_inicio, apr.fecha_fin, apr.activo
    FROM personal_reglas_ajustes apr
    JOIN personal p ON apr.personal_nombre = p.nombre
    WHERE p.servicio_id = 3 AND apr.codigo_regla = 'ASIGNACION_FIJA'
""")
for r in cursor.fetchall():
    print(f"Name: {r[0]}, Rule: {r[1]}, Action: {r[2]}, Params: {r[3]}, Start: {r[4]}, End: {r[5]}, Active: {r[6]}")

print("\n=== SERVICE 3: OTHER RULES IN personal_reglas_ajustes ===")
cursor.execute("""
    SELECT apr.personal_nombre, apr.codigo_regla, apr.accion, apr.parametros_json, apr.fecha_inicio, apr.fecha_fin, apr.activo
    FROM personal_reglas_ajustes apr
    JOIN personal p ON apr.personal_nombre = p.nombre
    WHERE p.servicio_id = 3 AND apr.codigo_regla != 'ASIGNACION_FIJA'
""")
for r in cursor.fetchall():
    print(f"Name: {r[0]}, Rule: {r[1]}, Action: {r[2]}, Params: {r[3]}, Start: {r[4]}, End: {r[5]}, Active: {r[6]}")

conn.close()
