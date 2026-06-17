import sqlite3
import json

conn = sqlite3.connect("cronograma_inteligente.db")
for row in conn.execute("SELECT codigo_regla, activo, parametros_json FROM servicios_reglas WHERE servicio_id = 1").fetchall():
    print(f"Regla: {row[0]}")
    print(f"  Activo: {row[1]}")
    try:
        parsed = json.loads(row[2])
        print(f"  Params: {json.dumps(parsed, indent=2)}")
    except Exception as e:
        print(f"  Raw Params: {row[2]} (Error parsing: {e})")
conn.close()
