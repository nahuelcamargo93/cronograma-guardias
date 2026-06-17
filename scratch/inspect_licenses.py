import sqlite3

DB_PATH = "c:/Users/asus/Desktop/Ryoko/cronograma_inteligente/cronograma_inteligente.db"

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    rows = cursor.execute("""
        SELECT tipo, fecha_inicio, fecha_fin 
        FROM licencias 
        WHERE nombre = 'ECHENIQUE ROCIO'
    """).fetchall()
    
    print("=== Licencias de ECHENIQUE ROCIO ===")
    for r in rows:
        print(f"Tipo: {r[0]}, Inicio: {r[1]}, Fin: {r[2]}")
        
    conn.close()

if __name__ == '__main__':
    main()
