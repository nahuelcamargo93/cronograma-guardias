import sqlite3

def main():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    print("=== TODAS LAS GUARDIAS (20 Y 21 DE JUNIO, CRONO 152) ===")
    query = """
        SELECT nombre, fecha, turno, horas 
        FROM guardias 
        WHERE cronograma_id = 152 
          AND fecha IN ('2026-06-20', '2026-06-21')
        ORDER BY fecha, turno, nombre
    """
    rows = cursor.execute(query).fetchall()
    for r in rows:
        print(f"Name: {repr(r[0])} | Fecha: {r[1]} | Turno: {r[2]} | Horas: {r[3]}")
        
    conn.close()

if __name__ == '__main__':
    main()
