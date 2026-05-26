import sqlite3
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import get_connection

def inspect():
    conn = get_connection()
    last_cr = conn.execute("SELECT id FROM cronogramas ORDER BY id DESC LIMIT 1").fetchone()
    cr_id = last_cr[0]
    
    fechas = ['2026-07-16', '2026-07-22', '2026-07-23']
    print(f"--- Guardias en {fechas} ---")
    rows = conn.execute("""
        SELECT g.fecha, g.turno, g.nombre, p.rol, p.categoria
        FROM guardias g
        JOIN personal p ON g.nombre = p.nombre
        WHERE g.cronograma_id = ? AND g.fecha IN ('2026-07-16', '2026-07-22', '2026-07-23')
        ORDER BY g.fecha, g.turno, g.nombre
    """, (cr_id,)).fetchall()
    
    for r in rows:
        print(f"Fecha: {r[0]}, Turno: {r[1]}, Nombre: {r[2]}, Rol: {r[3]}, Cat: {r[4]}")

if __name__ == "__main__":
    inspect()
