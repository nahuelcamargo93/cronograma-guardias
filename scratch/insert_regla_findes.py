import sqlite3
import json

db_path = "c:/Users/asus/Desktop/Ryoko/cronograma_inteligente/cronograma_inteligente.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Configuración de la regla MANEJO_FINDES para el servicio 2
parametros = {
  "modo": "HARD",
  "peso_soft": 100000,
  "por_disponibilidad": {
    "5": {"flr": 1, "completos": 2, "medios": 2},
    "4": {"flr": 1, "completos": 1, "medios": 2},
    "3": {"flr": 1, "completos": 1, "medios": 1},
    "2": {"flr": 0, "completos": 1, "medios": 1},
    "1": {"flr": 0, "completos": 2, "medios": 2}
  }
}

json_str = json.dumps(parametros)

# Deshabilitamos temporalmente o chequeamos si ya existe
cur.execute("SELECT id FROM servicios_reglas WHERE servicio_id = 2 AND codigo_regla = 'MANEJO_FINDES'")
row = cur.fetchone()

if row:
    cur.execute("UPDATE servicios_reglas SET parametros_json = ?, activo = 1 WHERE id = ?", (json_str, row[0]))
    print(f"Regla MANEJO_FINDES actualizada para servicio 2 (id={row[0]})")
else:
    cur.execute("INSERT INTO servicios_reglas (servicio_id, codigo_regla, parametros_json, activo) VALUES (2, 'MANEJO_FINDES', ?, 1)", (json_str,))
    print("Regla MANEJO_FINDES insertada para servicio 2")

conn.commit()
conn.close()
