import sys
import os
import sqlite3

sys.path.append(os.path.abspath('.'))
from database import queries as db_queries

reglas_servicio = db_queries.cargar_reglas_servicio(3)
print("--- Rules loaded by queries.cargar_reglas_servicio(3) ---")
for k, v in sorted(reglas_servicio.items()):
    print(f"  {k}: {v}")

print("\n--- Raw query on servicios_reglas for service_id = 3 ---")
conn = sqlite3.connect("cronograma_inteligente.db")
cur = conn.cursor()
cur.execute("""
    SELECT sr.codigo_regla, sr.parametros_json, sr.activo
    FROM servicios_reglas sr
    WHERE sr.servicio_id = 3
""")
for row in cur.fetchall():
    print(f"  Code: {row[0]} | Config: {row[1]} | Activo: {row[2]}")
conn.close()
