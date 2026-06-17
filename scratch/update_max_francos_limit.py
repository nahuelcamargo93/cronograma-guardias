import sqlite3
import json

DB_PATH = "cronograma_inteligente.db"

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    params = {"limite": 4}
    cursor.execute("""
        UPDATE servicios_reglas 
        SET parametros_json = ? 
        WHERE servicio_id = 2 AND codigo_regla = 'MAX_FRANCOS_SEMANA'
    """, (json.dumps(params),))
    
    conn.commit()
    conn.close()
    print("Límite de MAX_FRANCOS_SEMANA actualizado a 4 para Servicio 2.")

if __name__ == '__main__':
    main()
