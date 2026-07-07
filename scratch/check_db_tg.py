import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')

print("=== SERVICIOS REGLAS (servicio_id = 1) ===")
for r in conn.execute("SELECT sr.codigo_regla, sr.parametros_json, sr.activo FROM servicios_reglas sr WHERE sr.servicio_id = 1"):
    print(r[0], json.loads(r[1]) if r[1] else None, r[2])

print("\n=== ROLES REGLAS (servicio_id = 1) ===")
for r in conn.execute("SELECT rr.rol, rr.codigo_regla, rr.parametros_json, rr.activo FROM roles_reglas rr WHERE rr.servicio_id = 1"):
    print(r[0], r[1], json.loads(r[2]) if r[2] else None, r[3])

print("\n=== ALL PERSONAL REGLAS (servicio_id = 1) ===")
for r in conn.execute("""
    SELECT p.nombre, pr.codigo_regla, pr.parametros_json, pr.activo 
    FROM personal_reglas pr 
    JOIN personal p ON pr.personal_nombre = p.nombre
    WHERE p.servicio_id = 1
"""):
    print(r[0], r[1], json.loads(r[2]) if r[2] else None, r[3])

print("\n=== ALL PERSONAL REGLAS AJUSTES (servicio_id = 1) ===")
for r in conn.execute("""
    SELECT p.nombre, pra.codigo_regla, pra.fecha_inicio, pra.fecha_fin, pra.accion, pra.parametros_json, pra.activo 
    FROM personal_reglas_ajustes pra 
    JOIN personal p ON pra.personal_nombre = p.nombre
    WHERE p.servicio_id = 1
"""):
    print(r[0], r[1], r[2], r[3], r[4], json.loads(r[5]) if r[5] else None, r[6])

conn.close()
