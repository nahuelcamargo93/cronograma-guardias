import sqlite3
import sys

def set_mode(mode):
    conn = sqlite3.connect("cronograma_inteligente.db")
    cur = conn.cursor()
    
    # Read current parameters
    cur.execute("SELECT parametros_json FROM servicios_reglas WHERE servicio_id = 3 AND codigo_regla = 'EXACTO_FINDE_Y_DIA'")
    row = cur.fetchone()
    if not row:
        print("Rule not found")
        conn.close()
        return
        
    import json
    params = json.loads(row[0])
    params['modo'] = mode
    
    cur.execute(
        "UPDATE servicios_reglas SET parametros_json = ? WHERE servicio_id = 3 AND codigo_regla = 'EXACTO_FINDE_Y_DIA'",
        (json.dumps(params),)
    )
    conn.commit()
    print(f"Updated EXACTO_FINDE_Y_DIA mode to {mode}")
    conn.close()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        set_mode(sys.argv[1].upper())
    else:
        print("Provide mode: HARD or SOFT")
