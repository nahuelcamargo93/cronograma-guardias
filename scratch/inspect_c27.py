import sqlite3

def main():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    print("=== GUARDIAS ON JUNE 27 (CRONO 152) ===")
    query = """
        SELECT nombre, fecha, turno, horas 
        FROM guardias 
        WHERE cronograma_id = 152 
          AND fecha = '2026-06-27'
        ORDER BY turno, nombre
    """
    rows = cursor.execute(query).fetchall()
    for r in rows:
        print(f"Name: {repr(r[0])} | Fecha: {r[1]} | Turno: {r[2]} | Horas: {r[3]}")
        
    conn.close()

if __name__ == '__main__':
    main()
