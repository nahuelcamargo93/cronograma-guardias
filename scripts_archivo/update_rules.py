import sqlite3
import json

def update_database():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    # Rule 2: DESC_POST_NOCHE
    # Check if exists for service 2
    cursor.execute("SELECT id FROM servicios_reglas WHERE servicio_id = 2 AND regla_id = 2;")
    row = cursor.fetchone()
    if row:
        print("Updating DESC_POST_NOCHE for service 2...")
        cursor.execute("UPDATE servicios_reglas SET parametros_json = ? WHERE id = ?;", ('{"horas": 12}', row[0]))
    else:
        print("Inserting DESC_POST_NOCHE for service 2...")
        cursor.execute("INSERT INTO servicios_reglas (servicio_id, regla_id, parametros_json) VALUES (?, ?, ?);", (2, 2, '{"horas": 12}'))
        
    # Rule 1: MAX_HORAS_SEMANA
    # Check if exists for service 2
    cursor.execute("SELECT id FROM servicios_reglas WHERE servicio_id = 2 AND regla_id = 1;")
    row = cursor.fetchone()
    if row:
        print("Updating MAX_HORAS_SEMANA for service 2...")
        cursor.execute("UPDATE servicios_reglas SET parametros_json = ? WHERE id = ?;", ('{"limite": 36}', row[0]))
    else:
        print("Inserting MAX_HORAS_SEMANA for service 2...")
        cursor.execute("INSERT INTO servicios_reglas (servicio_id, regla_id, parametros_json) VALUES (?, ?, ?);", (2, 1, '{"limite": 36}'))
        
    conn.commit()
    print("Database updated successfully.")
    conn.close()

if __name__ == "__main__":
    update_database()
