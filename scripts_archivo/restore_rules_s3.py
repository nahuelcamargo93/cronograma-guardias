import sqlite3
import json

def restore_rules():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    # 1. Piso 144hs
    cursor.execute("INSERT OR REPLACE INTO servicios_reglas (servicio_id, regla_id, parametros_json) VALUES (3, 169, ?)", (json.dumps({"min_horas": 144}),))
    # 2. Descanso 48hs para G, 24hs para D/N
    cursor.execute("INSERT OR REPLACE INTO servicios_reglas (servicio_id, regla_id, parametros_json) VALUES (3, 167, ?)", (json.dumps({"por_turno": {"G": 48, "D": 24, "N": 24}}),))
    conn.commit()
    conn.close()
    print("Rules 169 and 167 restored for Service 3.")

if __name__ == "__main__":
    restore_rules()
