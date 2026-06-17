import sqlite3

DB_PATH = "c:/Users/asus/Desktop/Ryoko/cronograma_inteligente/cronograma_inteligente.db"

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("=== Conteo de Infracciones ===")
    rows = cursor.execute("""
        SELECT codigo_regla, COUNT(*) 
        FROM infracciones_debug 
        WHERE cronograma_id = 329 
        GROUP BY codigo_regla
    """).fetchall()
    for r in rows:
        print(f"Regla: {r[0]}, Cantidad: {r[1]}")
        
    print("\n=== Detalles por regla ===")
    for r in rows:
        regla = r[0]
        detalles = cursor.execute("""
            SELECT detalle 
            FROM infracciones_debug 
            WHERE cronograma_id = 329 AND codigo_regla = ?
            LIMIT 15
        """, (regla,)).fetchall()
        print(f"\n--- {regla} ---")
        for d in detalles:
            print(f"  * {d[0]}")
            
    conn.close()

if __name__ == '__main__':
    main()
