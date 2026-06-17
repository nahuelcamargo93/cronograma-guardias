import sqlite3

def main():
    conn = sqlite3.connect("cronograma_inteligente.db")
    cursor = conn.cursor()
    cursor.execute("SELECT codigo_regla, detalle FROM infracciones_debug WHERE cronograma_id = 467")
    rows = cursor.fetchall()
    
    print(f"Total infracciones detectadas: {len(rows)}")
    for idx, (regla, detalle) in enumerate(rows, 1):
        print(f"{idx}. Regla: {regla} | Detalle: {detalle}")
        
    conn.close()

if __name__ == "__main__":
    main()
