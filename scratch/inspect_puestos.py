import sqlite3
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import get_connection

def inspect():
    conn = get_connection()
    print("=== PERSONAL PUESTOS HABILITADOS ===")
    names = ['FERNANDEZ Claudia Elizabeth', 'GUERRIDO Noelia']
    for name in names:
        puestos = conn.execute("""
            SELECT p.nombre, p.id
            FROM personal_puestos pp
            JOIN puestos p ON pp.puesto_id = p.id
            WHERE pp.personal_nombre = ?
        """, (name,)).fetchall()
        print(f"\nEmployee: {name}")
        for pst in puestos:
            print(f"  Puesto: {pst[0]} (ID: {pst[1]})")

    print("\n=== ALL PUESTOS IN SERVICIO 4 ===")
    puestos = conn.execute("SELECT id, nombre FROM puestos WHERE servicio_id = 4").fetchall()
    for p in puestos:
        print(f"  Puesto ID: {p[0]}, Nombre: {p[1]}")

if __name__ == "__main__":
    inspect()
