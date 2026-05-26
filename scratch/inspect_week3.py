import sqlite3
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import get_connection

def inspect():
    conn = get_connection()
    last_cr = conn.execute("SELECT id FROM cronogramas ORDER BY id DESC LIMIT 1").fetchone()
    cr_id = last_cr[0]
    
    print("--- ASIIGNMENTS FOR 06-12 MONITORISTAS IN WEEK 3 (July 13 to 19) ---")
    
    group_06_12 = [
        "ALCARAZ Xavier", "OJEDA Miriam", "STEIMBRECHER Yolanda", 
        "LEDESMA PAZ Micaela", "MANSILLA Diego", "MESSINA Eduardo", 
        "RODRIGUEZ Maximiliano"
    ]
    
    # 1. Total shifts worked by each of them in Week 3
    print("\n[Total shifts in Week 3 per person]")
    rows = conn.execute("""
        SELECT nombre, COUNT(id)
        FROM guardias
        WHERE cronograma_id = ? AND fecha BETWEEN '2026-07-13' AND '2026-07-19'
        GROUP BY nombre
    """, (cr_id,)).fetchall()
    for r in rows:
        print(f"  {r[0]}: {r[1]} shifts")
        
    # 2. Detailed grid of who worked which day of Week 3
    print("\n[Grid of assignments]")
    days = [f"2026-07-{d}" for d in range(13, 20)]
    for day in days:
        assigned = conn.execute("""
            SELECT nombre, turno
            FROM guardias
            WHERE cronograma_id = ? AND fecha = ? AND nombre IN ({})
        """.format(",".join("?" for _ in group_06_12)), [cr_id, day] + group_06_12).fetchall()
        
        assigned_names = [f"{r[0]} ({r[1]})" for r in assigned]
        print(f"  {day}: {', '.join(assigned_names)}")

if __name__ == "__main__":
    inspect()
