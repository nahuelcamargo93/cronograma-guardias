import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')
conn.row_factory = sqlite3.Row

print("=== PERSONAL SERVICIO 1 ===")
for r in conn.execute("SELECT nombre, rol, categoria, activo FROM personal WHERE servicio_id = 1").fetchall():
    print(dict(r))

print("\n=== REGLAS SERVICIO 1 ===")
for r in conn.execute("SELECT codigo_regla, activo, parametros_json FROM servicios_reglas WHERE servicio_id = 1").fetchall():
    print(r['codigo_regla'], "Activo:", r['activo'], "Params:", r['parametros_json'])

print("\n=== REGLAS PERSONAL SERVICIO 1 ===")
for r in conn.execute("""
    SELECT pr.personal_nombre, pr.codigo_regla, pr.activo, pr.parametros_json
    FROM personal_reglas pr
    JOIN personal p ON pr.personal_nombre = p.nombre
    WHERE p.servicio_id = 1
""").fetchall():
    print(r['personal_nombre'], r['codigo_regla'], "Activo:", r['activo'], "Params:", r['parametros_json'])

print("\n=== AJUSTES PERSONAL REGLAS ===")
for r in conn.execute("""
    SELECT pra.personal_nombre, pra.codigo_regla, pra.fecha_inicio, pra.fecha_fin, pra.accion, pra.parametros_json, pra.activo
    FROM personal_reglas_ajustes pra
    JOIN personal p ON pra.personal_nombre = p.nombre
    WHERE p.servicio_id = 1 AND pra.activo = 1
""").fetchall():
    print(dict(r))

print("\n=== PUESTOS SERVICIO 1 ===")
for r in conn.execute("SELECT * FROM puestos WHERE servicio_id = 1").fetchall():
    print(dict(r))

print("\n=== TURNOS CONFIG SERVICIO 1 ===")
for r in conn.execute("SELECT * FROM turnos_config WHERE servicio_id = 1").fetchall():
    print(dict(r))

print("\n=== DEMANDA CONFIG SERVICIO 1 ===")
for r in conn.execute("""
    SELECT dc.*, p.nombre as puesto
    FROM demanda_config dc
    JOIN puestos p ON dc.puesto_id = p.id
    WHERE p.servicio_id = 1
""").fetchall():
    print(dict(r))


conn.close()
