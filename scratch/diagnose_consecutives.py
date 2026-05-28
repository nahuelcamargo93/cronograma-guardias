import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sqlite3
import datetime

def main():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    print("--- Matricadi Fridays in Crono 215 ---")
    query = """
        SELECT g.fecha, g.turno
        FROM guardias g
        WHERE g.cronograma_id = 215 AND g.nombre LIKE '%Matricadi%'
        ORDER BY g.fecha
    """
    rows = cursor.execute(query).fetchall()
    
    fridays_count = 0
    for r in rows:
        fecha_str = r[0]
        dt = datetime.datetime.strptime(fecha_str, "%Y-%m-%d")
        is_friday = (dt.weekday() == 4) # Friday is 4
        friday_marker = " [FRIDAY]" if is_friday else ""
        if is_friday:
            fridays_count += 1
        print(f"Fecha: {fecha_str} | Turno: {r[1]}{friday_marker}")
        
    print(f"\nTotal Fridays worked by Matricadi in Crono 215: {fridays_count}")
    
    conn.close()

if __name__ == '__main__':
    main()
