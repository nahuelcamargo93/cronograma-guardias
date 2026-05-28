import sqlite3
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import get_connection

def inspect():
    conn = get_connection()
    names = ['FERNANDEZ Claudia Elizabeth', 'GUERRIDO Noelia']
    
    print("=== PERSONAL DETAILS ===")
    for name in names:
        row = conn.execute("""
            SELECT nombre, categoria, rol, servicio_id, fecha_cumpleanos, es_madre, es_padre, regimen_trabajo, horas_mensuales_reglamentarias, activo
            FROM personal
            WHERE nombre = ?
        """, (name,)).fetchone()
        if row:
            print(f"\nName: {row[0]}")
            print(f"  Categoria: {row[1]}")
            print(f"  Rol: {row[2]}")
            print(f"  Servicio ID: {row[3]}")
            print(f"  Cumpleaños: {row[4]}")
            print(f"  Es madre: {row[5]}")
            print(f"  Es padre: {row[6]}")
            print(f"  Regimen: {row[7]}")
            print(f"  Horas mensuales reglamentarias: {row[8]}")
            print(f"  Activo: {row[9]}")
        else:
            print(f"\nName {name} not found.")

if __name__ == "__main__":
    inspect()
