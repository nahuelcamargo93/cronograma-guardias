import sqlite3
import json

def migrate():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    # Service 2 (Enfermeria UTI)
    # Turnos: M, MT, N, T, TN, TNN
    s2_config = {
        "por_turno": {
            "M": 12,
            "T": 12,
            "TN": 12,
            "N": 12,
            "TNN": 12,
            "MT": 12
        }
    }
    cursor.execute("""
        UPDATE servicios_reglas 
        SET parametros_json = ? 
        WHERE servicio_id = 2 AND regla_id = 167
    """, (json.dumps(s2_config),))
    
    # Service 3 (Area Medica UTI)
    # Turnos: G, D, N (G_Planta, G_Residente, etc)
    s3_config = {
        "por_turno": {
            "G": 48,
            "D": 24,
            "N": 24
        }
    }
    cursor.execute("""
        UPDATE servicios_reglas 
        SET parametros_json = ? 
        WHERE servicio_id = 3 AND regla_id = 167
    """, (json.dumps(s3_config),))
    
    conn.commit()
    conn.close()
    print("Migration of rest rules completed.")

if __name__ == "__main__":
    migrate()
