import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')
cur = conn.cursor()

SERVICIO_ID = 2
CODIGO_RELA = 'FINDES_COMPLETOS_Y_MEDIOS'

# 1. Ensure the rule is in the reglas_catalogo (just in case)
cur.execute("INSERT OR IGNORE INTO reglas_catalogo (codigo_regla, tipo, descripcion) VALUES (?, 'HARD', ?)",
            (CODIGO_RELA, 'Asegura la cantidad exacta de fines de semana completos y medios trabajados según la disponibilidad.'))

# 2. Suspend MIN_FINDES_MES for service 2 to avoid conflicts
cur.execute("SELECT parametros_json FROM servicios_reglas WHERE servicio_id = ? AND codigo_regla = 'MIN_FINDES_MES'", (SERVICIO_ID,))
row = cur.fetchone()
if row:
    params = json.loads(row[0])
    params['suspendida'] = True
    cur.execute("UPDATE servicios_reglas SET parametros_json = ? WHERE servicio_id = ? AND codigo_regla = 'MIN_FINDES_MES'",
                (json.dumps(params), SERVICIO_ID))
    print("MIN_FINDES_MES suspendida para servicio 2.")

# 3. Add or update FINDES_COMPLETOS_Y_MEDIOS for service 2
config_json = {
    "por_disponibilidad": {
        "5": { "completos": 3, "medios": 1 },
        "4": { "completos": 2, "medios": 1 },
        "3": { "completos": 1, "medios": 1 },
        "2": { "completos": 1, "medios": 0 },
        "1": { "completos": 0, "medios": 1 },
        "0": { "completos": 0, "medios": 0 }
    }
}

cur.execute("SELECT id FROM servicios_reglas WHERE servicio_id = ? AND codigo_regla = ?", (SERVICIO_ID, CODIGO_RELA))
existing = cur.fetchone()
if existing:
    cur.execute("UPDATE servicios_reglas SET parametros_json = ? WHERE id = ?", (json.dumps(config_json), existing[0]))
    print(f"Regla {CODIGO_RELA} actualizada para servicio 2.")
else:
    cur.execute("INSERT INTO servicios_reglas (servicio_id, codigo_regla, parametros_json) VALUES (?, ?, ?)",
                (SERVICIO_ID, CODIGO_RELA, json.dumps(config_json)))
    print(f"Regla {CODIGO_RELA} creada para servicio 2.")

conn.commit()
conn.close()
