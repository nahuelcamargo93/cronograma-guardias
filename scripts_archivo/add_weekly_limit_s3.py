import sqlite3
import json

def add_weekly_limit():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO servicios_reglas (servicio_id, regla_id, parametros_json) VALUES (3, 1, ?)", (json.dumps({"limite": 60}),))
    conn.commit()
    conn.close()
    print("Added MAX_HORAS_SEMANA (60hs) to Service 3.")

if __name__ == "__main__":
    add_weekly_limit()
