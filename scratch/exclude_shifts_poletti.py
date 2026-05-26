import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')
cur = conn.cursor()

NOMBRE = 'POLETTI NATALIA'

# 1. Add EXCLUIR_TURNOS rule for Poletti
excluir_params = [{"turnos": ["M", "T", "TN", "N"], "dias": [0,1,2,3,4,5,6]}]
cur.execute("""
    INSERT INTO personal_reglas (personal_nombre, codigo_regla, parametros_json)
    VALUES (?, 'EXCLUIR_TURNOS', ?)
    ON CONFLICT(personal_nombre, codigo_regla) DO UPDATE SET parametros_json = excluded.parametros_json
""", (NOMBRE, json.dumps(excluir_params)))
print("Regla EXCLUIR_TURNOS creada para POLETTI NATALIA.")

# 2. Suspend PENALIZACION_TURNO_AUSENTE (which controls monthly rotation) for Poletti
suspend_params = {"suspendida": True}
cur.execute("""
    INSERT INTO personal_reglas (personal_nombre, codigo_regla, parametros_json)
    VALUES (?, 'PENALIZACION_TURNO_AUSENTE', ?)
    ON CONFLICT(personal_nombre, codigo_regla) DO UPDATE SET parametros_json = excluded.parametros_json
""", (NOMBRE, json.dumps(suspend_params)))
print("Regla PENALIZACION_TURNO_AUSENTE suspendida para POLETTI NATALIA.")

conn.commit()
conn.close()
