import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

print("=== REGLAS SERVICIO 1 ===")
cursor.execute("""
    SELECT id, codigo_regla, activo, parametros_json 
    FROM servicios_reglas 
    WHERE servicio_id = 1
""")
for row in cursor.fetchall():
    print(f"ID: {row[0]} | Regla: {row[1]} | Activo: {row[2]}")
    try:
        parsed = json.loads(row[3])
        print(f"  Params: {json.dumps(parsed, indent=2)}")
    except:
        print(f"  Params (raw): {row[3]}")

conn.close()
