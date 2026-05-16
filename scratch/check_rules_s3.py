import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

SERVICIO_ID = 3

print(f"--- Rules for Service {SERVICIO_ID} ---")
cursor.execute("""
    SELECT rc.codigo_regla, sr.parametros_json
    FROM servicios_reglas sr
    JOIN reglas_catalogo rc ON sr.regla_id = rc.id
    WHERE sr.servicio_id = ?
""", (SERVICIO_ID,))

for row in cursor.fetchall():
    print(row)

print(f"\n--- Global Rules (Org 1) ---")
cursor.execute("""
    SELECT rc.codigo_regla, or_r.parametros_json
    FROM organizaciones_reglas or_r
    JOIN reglas_catalogo rc ON or_r.regla_id = rc.id
    WHERE or_r.organizacion_id = 1
""")
for row in cursor.fetchall():
    print(row)

conn.close()
