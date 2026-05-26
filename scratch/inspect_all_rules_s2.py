import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

# Get all rules for Servicio 2
cursor.execute("""
    SELECT sr.id, rc.codigo_regla, sr.parametros_json
    FROM servicios_reglas sr
    JOIN reglas_catalogo rc ON sr.regla_id = rc.id
    WHERE sr.servicio_id = 2
""")
rows = cursor.fetchall()
print("=== SERVICIO 2 RULES ===")
for r in rows:
    print(f"Rule: {r[1]}, Params: {r[2]}")

print("\n=== ORGANIZACION RULES ===")
# Let's see if there are organization level rules
cursor.execute("""
    SELECT orgo.id, rc.codigo_regla, orgo.parametros_json
    FROM organizaciones_reglas orgo
    JOIN reglas_catalogo rc ON orgo.regla_id = rc.id
""")
rows = cursor.fetchall()
for r in rows:
    print(f"Rule: {r[1]}, Params: {r[2]}")

conn.close()
