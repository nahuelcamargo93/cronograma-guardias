import sqlite3
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import get_connection

def inspect():
    conn = get_connection()
    name = 'SUAREZ Carolina'
    
    print(f"=== DETAILS FOR {name} ===")
    emp = conn.execute("SELECT nombre, categoria, rol, activo FROM personal WHERE nombre = ?", (name,)).fetchone()
    print(f"Emp: {emp}")
    
    print("\n=== RULES IN personal_reglas ===")
    rules = conn.execute("SELECT codigo_regla, parametros_json, activo FROM personal_reglas WHERE personal_nombre = ?", (name,)).fetchall()
    for r in rules:
        print(f"  Regla: {r[0]} | Params: {r[1]} | Activo: {r[2]}")
        
    print("\n=== ADJUSTMENTS IN personal_reglas_ajustes ===")
    adjustments = conn.execute("SELECT codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo FROM personal_reglas_ajustes WHERE personal_nombre = ?", (name,)).fetchall()
    for a in adjustments:
        print(f"  Regla: {a[0]} | Range: {a[1]} to {a[2]} | Accion: {a[3]} | Params: {a[4]} | Activo: {a[5]}")

    print("\n=== SERVICE RULES FOR SERVICIO 4 ===")
    srv_rules = conn.execute("SELECT codigo_regla, parametros_json, activo FROM servicios_reglas WHERE servicio_id = 4").fetchall()
    for sr in srv_rules:
        print(f"  Regla: {sr[0]} | Params: {sr[1]} | Activo: {sr[2]}")

if __name__ == "__main__":
    inspect()
