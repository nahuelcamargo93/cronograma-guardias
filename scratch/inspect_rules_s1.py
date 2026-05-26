import sqlite3
import json

conn = sqlite3.connect("cronograma_inteligente.db")
conn.row_factory = sqlite3.Row

print("--- RULES FOR SERVICE 1 ---")
cur = conn.execute("""
    SELECT sr.*, rc.descripcion 
    FROM servicios_reglas sr
    JOIN reglas_catalogo rc ON sr.codigo_regla = rc.codigo_regla
    WHERE sr.servicio_id = 1
""")
for r in cur:
    print(f"Rule: {r['codigo_regla']:25} | Params: {r['parametros_json']} | Desc: {r['descripcion']}")
    
conn.close()
