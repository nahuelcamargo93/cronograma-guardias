import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')
cur = conn.cursor()
cur.execute("""
    SELECT codigo_regla, parametros_json, activo
    FROM servicios_reglas
    WHERE servicio_id = 1
""")
for cod, params, act in cur.fetchall():
    print(f"Regla: {cod} (Activa: {act})")
    try:
        parsed = json.loads(params) if params else {}
        print(f"  Params: {json.dumps(parsed, indent=2)}")
    except:
        print(f"  Params raw: {params}")

print("\n--- EJEMPLOS DE REGLAS DE PERSONAL DEL SERVICIO 1 ---")
cur.execute("""
    SELECT pr.personal_nombre, pr.codigo_regla, pr.parametros_json
    FROM personal_reglas pr
    JOIN personal p ON pr.personal_nombre = p.nombre
    WHERE p.servicio_id = 1 AND pr.activo = 1
    LIMIT 10
""")
for nom, cod, params in cur.fetchall():
    print(f"Empleado: {nom} | Regla: {cod}")
    try:
        parsed = json.loads(params) if params else {}
        print(f"  Params: {json.dumps(parsed, indent=2)}")
    except:
        print(f"  Params raw: {params}")

conn.close()
