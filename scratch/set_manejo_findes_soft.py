import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')
cur = conn.cursor()

# Configuración SOFT con peso 10000
parametros = {
  "modo": "SOFT",
  "peso_soft": 10000,
  "por_disponibilidad": {
    "5": {"flr": 0, "completos": 2, "medios": 1},
    "4": {"flr": 0, "completos": 1, "medios": 1},
    "3": {"flr": 0, "completos": 1, "medios": 1},
    "2": {"flr": 1, "completos": 1, "medios": 1},
    "1": {"flr": 0, "completos": 1, "medios": 0}
  }
}

json_str = json.dumps(parametros)

cur.execute("""
    UPDATE servicios_reglas 
    SET parametros_json = ? 
    WHERE servicio_id = 1 AND codigo_regla = 'MANEJO_FINDES'
""", (json_str,))

conn.commit()
print("Regla MANEJO_FINDES actualizada a SOFT para el servicio 1.")
conn.close()
