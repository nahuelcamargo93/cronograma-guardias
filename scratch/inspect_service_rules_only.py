import sqlite3
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import get_connection

def inspect():
    conn = get_connection()
    print("--- SERVICES RULES ---")
    rows = conn.execute("SELECT codigo_regla, parametros_json, activo FROM servicios_reglas WHERE servicio_id = 4").fetchall()
    for r in rows:
        if r[2] == 1:
            print(f"RULE: {r[0]} (Active)")
            print(f"  Params: {r[1]}")
        else:
            print(f"RULE: {r[0]} (Inactive)")

if __name__ == "__main__":
    inspect()
