import sqlite3
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import get_connection

def inspect():
    conn = get_connection()
    res = conn.execute("""
        SELECT p.nombre, p.categoria, p.rol, pst.nombre
        FROM personal_puestos pp
        JOIN personal p ON pp.personal_nombre = p.nombre
        JOIN puestos pst ON pp.puesto_id = pst.id
        WHERE p.servicio_id = 4 AND pst.id = 31
    """).fetchall()
    
    print("=== EMPLOYEES WITH SUPERVISOR HABILITADO (PUESTO 31) ===")
    for row in res:
        print(f"Name: {row[0]:<35} | Cat: {row[1]} | Rol: {row[2]} | Puesto: {row[3]}")
        
if __name__ == "__main__":
    inspect()
