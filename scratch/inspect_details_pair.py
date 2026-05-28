import sqlite3
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import get_connection

def inspect():
    conn = get_connection()
    names = ['FERNANDEZ Claudia Elizabeth', 'GUERRIDO Noelia']
    
    print("=== LICENCIAS ===")
    for name in names:
        lics = conn.execute("SELECT tipo, fecha_inicio, fecha_fin FROM licencias WHERE nombre = ?", (name,)).fetchall()
        print(f"\nEmployee: {name}")
        for l in lics:
            print(f"  Tipo: {l[0]}, Inicio: {l[1]}, Fin: {l[2]}")
            
    print("\n=== REGLAS PERSONAL (TABLA personal_reglas) ===")
    for name in names:
        rules = conn.execute("SELECT codigo_regla, parametros_json, activo FROM personal_reglas WHERE personal_nombre = ?", (name,)).fetchall()
        print(f"\nEmployee: {name}")
        for r in rules:
            print(f"  Regla: {r[0]}, Params: {r[1]}, Activo: {r[2]}")
            
    print("\n=== REGLAS PERSONAL AJUSTES (TABLA personal_reglas_ajustes) ===")
    for name in names:
        rules_aj = conn.execute("""
            SELECT codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo 
            FROM personal_reglas_ajustes 
            WHERE personal_nombre = ?
        """, (name,)).fetchall()
        print(f"\nEmployee: {name}")
        for r in rules_aj:
            print(f"  Regla: {r[0]}, Inicio: {r[1]}, Fin: {r[2]}, Accion: {r[3]}, Params: {r[4]}, Activo: {r[5]}")

if __name__ == "__main__":
    inspect()
