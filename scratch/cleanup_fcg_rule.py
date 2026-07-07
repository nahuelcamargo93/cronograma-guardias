import sqlite3
import json

def main():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cur = conn.execute('SELECT parametros_json FROM servicios_reglas WHERE servicio_id = 2 AND codigo_regla = "EXCLUIR_TURNOS"')
    row = cur.fetchone()
    if row:
        params = json.loads(row[0])
        # Filter out FCG exclusions
        new_params = [p for p in params if "FCG" not in p.get("turnos", [])]
        new_json = json.dumps(new_params)
        conn.execute('UPDATE servicios_reglas SET parametros_json = ? WHERE servicio_id = 2 AND codigo_regla = "EXCLUIR_TURNOS"', (new_json,))
        conn.commit()
        print("Updated EXCLUIR_TURNOS for servicio 2:", new_json)
    else:
        print("No EXCLUIR_TURNOS rule found for servicio 2.")

if __name__ == '__main__':
    main()
