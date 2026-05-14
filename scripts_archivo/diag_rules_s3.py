import sqlite3
import json

def adjust_rules():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    # Activar 169 (Piso 144hs)
    cursor.execute("INSERT OR REPLACE INTO servicios_reglas (servicio_id, regla_id, parametros_json) VALUES (3, 169, ?)", (json.dumps({"min_horas": 144}),))
    # Desactivar 167 (Descanso)
    cursor.execute("DELETE FROM servicios_reglas WHERE servicio_id = 3 AND regla_id = 167")
    conn.commit()
    conn.close()
    print("Re-enabled Rule 169 (144hs) and disabled Rule 167 (Rest) for Service 3.")

if __name__ == "__main__":
    adjust_rules()
