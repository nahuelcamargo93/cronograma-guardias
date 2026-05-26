import sqlite3
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import get_connection

def inspect():
    conn = get_connection()
    last_cr = conn.execute("SELECT id, fecha_inicio, fecha_fin FROM cronogramas ORDER BY id DESC LIMIT 1").fetchone()
    cr_id, fi, ff = last_cr
    print(f"Cronograma ID: {cr_id} ({fi} to {ff})")
    
    # Finde dates in July 2026:
    # 4, 5, 9 (holiday), 11, 12, 18, 19, 25, 26
    findes = ['2026-07-04', '2026-07-05', '2026-07-09', '2026-07-11', '2026-07-12', '2026-07-18', '2026-07-19', '2026-07-25', '2026-07-26']
    
    # We want to see how many weekend shifts each person worked
    rows = conn.execute("""
        SELECT g.nombre, p.rol, COUNT(g.id), SUM(g.horas)
        FROM guardias g
        JOIN personal p ON g.nombre = p.nombre
        WHERE g.cronograma_id = ? AND g.fecha IN ({})
        GROUP BY g.nombre, p.rol
        ORDER BY p.rol, g.nombre
    """.format(",".join("?" for _ in findes)), [cr_id] + findes).fetchall()
    
    print("\n[Weekend shifts per person (out of 9 possible weekend/holiday days)]")
    for r in rows:
        print(f"  {r[0]} ({r[1]}): {r[2]} shifts, {r[3]} hours")

if __name__ == "__main__":
    inspect()
