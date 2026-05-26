import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')
cur = conn.cursor()

print("--- Rules configured for Service 3 in servicios_reglas ---")
cur.execute("""
    SELECT sr.id, rc.codigo_regla, sr.parametros_json
    FROM servicios_reglas sr
    JOIN reglas_catalogo rc ON sr.regla_id = rc.id
    WHERE sr.servicio_id = 3
""")
for row in cur.fetchall():
    print(row)
