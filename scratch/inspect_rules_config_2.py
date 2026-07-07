import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')

rows = conn.execute("""
    SELECT codigo_regla, parametros_json, activo
    FROM servicios_reglas
    WHERE servicio_id = 2 AND codigo_regla IN ('DISTANCIA_MINIMA_TIPO_SEMANA', 'REPETICION_TIPO_SEMANA', 'NO_REPETIR_TURNO_CONSECUTIVO')
""").fetchall()

for code, params, active in rows:
    print(f"=== REGLA: {code} (Activa: {active}) ===")
    try:
        parsed = json.loads(params)
        print(json.dumps(parsed, indent=2))
    except Exception as e:
        print("Raw params:", params)

conn.close()
