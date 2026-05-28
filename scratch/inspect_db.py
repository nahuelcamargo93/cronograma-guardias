import sqlite3
import json

def inspect():
    conn = sqlite3.connect("cronograma_inteligente.db")
    cur = conn.cursor()
    
    print("=== servicios_reglas ===")
    cur.execute("SELECT * FROM servicios_reglas WHERE servicio_id = 3")
    for row in cur.fetchall():
        print(row)
        
    print("\n=== servicios_reglas_ajustes ===")
    try:
        cur.execute("SELECT * FROM servicios_reglas_ajustes")
        for row in cur.fetchall():
            print(row)
    except Exception as e:
        print("Error reading servicios_reglas_ajustes:", e)
        
    print("\n=== reglas_catalogo ===")
    cur.execute("SELECT * FROM reglas_catalogo")
    for row in cur.fetchall():
        print(row)
        
    conn.close()

if __name__ == '__main__':
    inspect()
