import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

print("=== REGLAS DEL SERVICIO 2 EN LA DB ===")
rows = cursor.execute("""
    SELECT sr.codigo_regla, sr.activo, sr.parametros_json
    FROM servicios_reglas sr
    WHERE sr.servicio_id = 2
""").fetchall()

for r in rows:
    print(f"\nRegla: {r[0]} | Activa: {r[1]}")
    try:
        print(json.dumps(json.loads(r[2]), indent=2))
    except:
        print(r[2])

conn.close()
