import sqlite3
import json

def migrate_kine():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    # Service 1 (Kinesiologia)
    # Turnos: Dia_UCO, Dia_UTI, Mañana_UCO, Mañana_UTI, Mañana_especial, Noche, Tarde_UCO, Tarde_UTI, Tarde_especial
    s1_config = {
        "por_turno": {
            "Noche": 24,
            "Dia": 12,
            "Mañana": 12,
            "Tarde": 12
        }
    }
    
    # Check if rule 167 exists for service 1
    cursor.execute("SELECT id FROM servicios_reglas WHERE servicio_id = 1 AND regla_id = 167")
    exists = cursor.fetchone()
    
    if exists:
        cursor.execute("""
            UPDATE servicios_reglas 
            SET parametros_json = ? 
            WHERE servicio_id = 1 AND regla_id = 167
        """, (json.dumps(s1_config),))
    else:
        cursor.execute("""
            INSERT INTO servicios_reglas (servicio_id, regla_id, parametros_json)
            VALUES (?, ?, ?)
        """, (1, 167, json.dumps(s1_config)))
    
    # Remove rule 2 (DESC_POST_NOCHE) from ALL services
    print("Removing rule 2 (DESC_POST_NOCHE) from all services...")
    cursor.execute("DELETE FROM servicios_reglas WHERE regla_id = 2")
    
    conn.commit()
    conn.close()
    print("Migration of Service 1 and removal of rule 2 completed.")

if __name__ == "__main__":
    migrate_kine()
