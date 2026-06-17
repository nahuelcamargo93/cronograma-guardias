import sqlite3
import json

db_path = "cronograma_inteligente.db"

def inspect():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Reglas servicio
    print("--- Ajustes Reglas Servicio ---")
    cursor.execute("""
        SELECT servicio_id, codigo_regla, activo, parametros_json
        FROM servicios_reglas
        WHERE servicio_id = 2 AND codigo_regla = 'ESQUEMA_SEMANAL_ENFERMERIA'
    """)
    rows = cursor.fetchall()
    for r in rows:
        print(f"Servicio: {r[0]}, Regla: {r[1]}, Activo: {r[2]}, Parametros: {r[3]}")
        
    conn.close()

if __name__ == "__main__":
    inspect()
