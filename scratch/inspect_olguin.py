import sqlite3

DB_PATH = "c:/Users/asus/Desktop/Ryoko/cronograma_inteligente/cronograma_inteligente.db"

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    rows = cursor.execute("""
        SELECT fecha, turno, horas 
        FROM guardias 
        WHERE cronograma_id = 329 AND nombre = 'OLGUIN LUCIA' AND fecha BETWEEN '2026-07-06' AND '2026-07-12'
        ORDER BY fecha
    """).fetchall()
    
    print("=== Guardia de OLGUIN LUCIA en Semana 28 ===")
    for r in rows:
        print(f"Fecha: {r[0]}, Turno: {r[1]}, Horas: {r[2]}")
        
    conn.close()

if __name__ == '__main__':
    main()
