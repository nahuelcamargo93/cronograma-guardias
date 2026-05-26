import sqlite3
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import get_connection

def inspect():
    conn = get_connection()
    last_cr = conn.execute("SELECT id FROM cronogramas ORDER BY id DESC LIMIT 1").fetchone()
    cr_id = last_cr[0]
    
    cat_a = [
        "ESCUDERO Gabriela", "FERNANDEZ Celeste Ivana", "FERNANDEZ Juan Emir", 
        "FLORES Enzo", "KOPRIVSEK Francisco"
    ]
    
    print("--- CATEGORY A GUARDIAS IN JUNE 2026 ---")
    rows = conn.execute("""
        SELECT g.fecha, g.turno, g.nombre, g.es_finde
        FROM guardias g
        WHERE g.cronograma_id = ? AND g.nombre IN ({})
        ORDER BY g.nombre, g.fecha
    """.format(",".join("?" for _ in cat_a)), [cr_id] + cat_a).fetchall()
    
    for r in rows:
        if r[3] == 1:
            print(f"  {r[2]}: {r[0]} ({r[1]}) - es_finde={r[3]} (!!!)")
        else:
            # print(f"  {r[2]}: {r[0]} ({r[1]})")
            pass

if __name__ == "__main__":
    inspect()
