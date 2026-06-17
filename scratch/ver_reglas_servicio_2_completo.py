import sqlite3
import json

def list_rules():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    print("=== Reglas activas para el Servicio 2 (Enfermería) ===")
    cursor.execute("""
        SELECT codigo_regla, parametros_json
        FROM servicios_reglas 
        WHERE servicio_id = 2 AND activo = 1;
    """)
    for r in cursor.fetchall():
        print(f"Regla: {r[0]} | Params: {r[1]}")
        
    print("\n=== Reglas personales para Natalia Polleti ===")
    cursor.execute("""
        SELECT codigo_regla, parametros_json
        FROM personal_reglas 
        WHERE personal_nombre = 'POLETTI NATALIA' AND activo = 1;
    """)
    for r in cursor.fetchall():
        print(f"Regla: {r[0]} | Params: {r[1]}")
        
    conn.close()

if __name__ == "__main__":
    list_rules()
