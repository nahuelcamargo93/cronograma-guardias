import sqlite3

def main():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    target_dates = ['2026-06-05', '2026-06-16', '2026-06-26', '2026-06-27']
    print("=== TODAS LAS GUARDIAS EN ESTAS FECHAS ===")
    query = """
        SELECT nombre, fecha, turno, horas, es_finde
        FROM guardias
        WHERE cronograma_id = 152
          AND fecha IN (?, ?, ?, ?)
        ORDER BY fecha, turno, nombre
    """
    rows = cursor.execute(query, target_dates).fetchall()
    for r in rows:
        print(f"Name: {repr(r[0])} | Fecha: {r[1]} | Turno: {r[2]} | Horas: {r[3]} | es_finde: {r[4]}")
        
    conn.close()

if __name__ == '__main__':
    main()
