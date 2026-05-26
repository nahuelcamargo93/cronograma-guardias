import sqlite3
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import get_connection

def inspect():
    conn = get_connection()
    
    print("\n--- REGLAS DE SERVICIO (SERVICIO 4) ---")
    rows = conn.execute("SELECT codigo_regla, parametros_json, activo FROM servicios_reglas WHERE servicio_id = 4").fetchall()
    for r in rows:
        print(f"Regla: {r[0]}, Activo: {r[2]}")
        print(f"  Params: {r[1]}")
        
    print("\n--- REGLAS INDIVIDUALES DE PERSONAL (SERVICIO 4) ---")
    rows_p = conn.execute("""
        SELECT pr.personal_nombre, pr.codigo_regla, pr.parametros_json, pr.activo 
        FROM personal_reglas pr
        JOIN personal p ON pr.personal_nombre = p.nombre
        WHERE p.servicio_id = 4 AND pr.activo = 1
    """).fetchall()
    for r in rows_p:
        print(f"Pers: {r[0]}, Regla: {r[1]}, Activo: {r[3]}")
        print(f"  Params: {r[2]}")

if __name__ == "__main__":
    inspect()
