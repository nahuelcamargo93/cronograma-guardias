import sqlite3
import json

DB_PATH = "c:/Users/asus/Desktop/Ryoko/cronograma_inteligente/cronograma_inteligente.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("=== Reglas del Servicio 2 ===")
rows = cursor.execute("""
    SELECT codigo_regla, parametros_json, activo
    FROM servicios_reglas
    WHERE servicio_id = 2 AND activo = 1
""").fetchall()

for r in rows:
    print(f"\nRegla: {r[0]}, Activo: {r[2]}")
    try:
        parsed = json.loads(r[1])
        print(json.dumps(parsed, indent=2))
    except:
        print(r[1])

conn.close()
