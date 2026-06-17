import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

print("=== ASIGNACIONES FIJAS EN JULIO 2026 (SERVICIO 3) ===")
# Let's get rules from personal_reglas for servicio_id = 3 and rule = ASIGNACION_FIJA
cursor.execute("""
    SELECT p.nombre, pr.parametros_json
    FROM personal_reglas pr
    JOIN personal p ON pr.personal_nombre = p.nombre
    WHERE p.servicio_id = 3 AND pr.codigo_regla = 'ASIGNACION_FIJA' AND pr.activo = 1
""")
for name, params in cursor.fetchall():
    print(f"- Empleado: {name}")
    try:
        parsed = json.loads(params)
        if isinstance(parsed, list):
            for asig in parsed:
                print(f"  * {asig}")
        else:
            print(f"  * {parsed}")
    except Exception as e:
        print(f"  * Error parsing: {params}")

conn.close()
