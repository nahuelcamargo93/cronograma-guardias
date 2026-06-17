import sqlite3
import json
import time

db_path = "cronograma_inteligente.db"

# Usamos un timeout más largo para esperar si la base de datos está bloqueada
conn = sqlite3.connect(db_path, timeout=30.0)
cur = conn.cursor()

parametros = {
  "modo": "SOFT",
  "peso_soft": 10000,
  "por_disponibilidad": {
    "5": {"flr": 0, "completos": 2, "medios": 1},
    "4": {"flr": 0, "completos": 1, "medios": 1},
    "3": {"flr": 0, "completos": 1, "medios": 1},
    "2": {"flr": 0, "completos": 1, "medios": 1},
    "1": {"flr": 0, "completos": 1, "medios": 0}
  },
  "nivelacion_historica": {
    "activo": True,
    "tipo": "ANUAL",
    "fecha_inicio": "2026-07-01"
  }
}

json_str = json.dumps(parametros)

try:
    # Comprobar si ya existe
    cur.execute("SELECT id FROM servicios_reglas WHERE servicio_id = 1 AND codigo_regla = 'MANEJO_FINDES'")
    row = cur.fetchone()

    if row:
        cur.execute("UPDATE servicios_reglas SET parametros_json = ?, activo = 1 WHERE id = ?", (json_str, row[0]))
        print(f"Regla MANEJO_FINDES actualizada para servicio 1 (id={row[0]})")
    else:
        cur.execute("INSERT INTO servicios_reglas (servicio_id, codigo_regla, parametros_json, activo) VALUES (1, 'MANEJO_FINDES', ?, 1)", (json_str,))
        print("Regla MANEJO_FINDES insertada para servicio 1")

    conn.commit()
    print("Transacción commited con éxito.")
except Exception as e:
    print(f"Error al operar la base de datos: {e}")
finally:
    conn.close()
