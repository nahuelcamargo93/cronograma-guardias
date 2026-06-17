import sqlite3
import json

DB_PATH = "c:/Users/asus/Desktop/Ryoko/cronograma_inteligente/cronograma_inteligente.db"

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    rows = cursor.execute("""
        SELECT codigo_regla, parametros_json, activo 
        FROM servicios_reglas 
        WHERE servicio_id = 2
    """).fetchall()
    
    print("=== Reglas del Servicio 2 ===")
    for r in rows:
        print(f"Regla: {r[0]}, Activo: {r[2]}")
        print(f"  Params: {r[1]}")
        
    conn.close()

if __name__ == '__main__':
    main()
