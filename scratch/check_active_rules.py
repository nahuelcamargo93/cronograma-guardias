import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("=== REGLAS CONFIGURADAS PARA SERVICIO 2 ===")
cursor.execute("""
    SELECT sr.id, rc.codigo_regla, sr.parametros_json, (1) as activa
    FROM servicios_reglas sr
    JOIN reglas_catalogo rc ON sr.regla_id = rc.id
    WHERE sr.servicio_id = 2
""")
for row in cursor.fetchall():
    print(dict(row))

print("\n=== AJUSTES REGLAS PERSONAL PARA SERVICIO 2 ===")
cursor.execute("""
    SELECT pr.personal_nombre as nombre, rc.codigo_regla, pr.parametros_json, (0) as suspendida
    FROM personal_reglas pr
    JOIN personal p ON pr.personal_nombre = p.nombre
    JOIN reglas_catalogo rc ON pr.regla_id = rc.id
    WHERE p.servicio_id = 2
""")
for row in cursor.fetchall():
    print(dict(row))


conn.close()
