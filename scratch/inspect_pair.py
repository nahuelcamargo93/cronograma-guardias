import sqlite3
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import get_connection

def inspect():
    conn = get_connection()
    print("=== PERSONAL FOR SERVICIO 4 ===")
    res = conn.execute("SELECT nombre, categoria, rol, activo FROM personal WHERE servicio_id = 4").fetchall()
    for row in res:
        print(f"Name: {row[0]!r} | Categoria: {row[1]!r} | Rol: {row[2]!r} | Activo: {row[3]!r}")
        
    print("\n=== RULES FOR PERSONAL_ASOCIADO ===")
    res = conn.execute("SELECT codigo_regla, parametros_json, activo FROM servicios_reglas WHERE servicio_id = 4 AND codigo_regla = 'PERSONAL_ASOCIADO'").fetchall()
    for row in res:
        print(f"Regla: {row[0]} | Activo: {row[2]}")
        print(f"Params: {row[1]}")

if __name__ == "__main__":
    inspect()
