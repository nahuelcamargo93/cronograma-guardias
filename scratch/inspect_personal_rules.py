import sqlite3
import json

conn = sqlite3.connect("cronograma_inteligente.db")
conn.row_factory = sqlite3.Row

print("--- PERSONAL RULES ---")
cur = conn.execute("""
    SELECT personal_nombre, codigo_regla, parametros_json
    FROM personal_reglas
    WHERE personal_nombre IN (SELECT nombre FROM personal WHERE servicio_id = 1)
""")
for r in cur:
    print(f"Name: {r['personal_nombre']:25} | Rule: {r['codigo_regla']:25} | Params: {r['parametros_json']}")

conn.close()
