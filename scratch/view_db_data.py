import os
import sys
import json

# Ensure project root is in path
script_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else '.'
project_root = os.path.abspath(os.path.join(script_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from database.connection import get_connection

def inspect():
    with get_connection() as conn:
        print("=== REGLAS DE SERVICIO 1 ===")
        rows = conn.execute("""
            SELECT codigo_regla, parametros_json, activo 
            FROM servicios_reglas 
            WHERE servicio_id = 1
        """).fetchall()
        for r in rows:
            print(f"Regla: {r[0]}, Activo: {r[2]}")
            print(f"  Params: {r[1]}")
            
        print("\n=== REGLAS DE PERSONAL ===")
        rows = conn.execute("""
            SELECT pr.personal_nombre, pr.codigo_regla, pr.parametros_json, pr.activo 
            FROM personal_reglas pr
            JOIN personal p ON pr.personal_nombre = p.nombre
            WHERE p.servicio_id = 1
        """).fetchall()
        for r in rows:
            print(f"Empleado: {r[0]}, Regla: {r[1]}, Activo: {r[3]}")
            print(f"  Params: {r[2]}")

        print("\n=== AJUSTES REGLAS PERSONAL ===")
        rows = conn.execute("""
            SELECT pra.personal_nombre, pra.codigo_regla, pra.fecha_inicio, pra.fecha_fin, pra.accion, pra.parametros_json, pra.activo 
            FROM personal_reglas_ajustes pra
            JOIN personal p ON pra.personal_nombre = p.nombre
            WHERE p.servicio_id = 1 AND pra.activo = 1
        """).fetchall()
        for r in rows:
            print(f"Empleado: {r[0]}, Regla: {r[1]}, Fechas: {r[2]} -> {r[3]}, Accion: {r[4]}")
            print(f"  Params: {r[5]}")

if __name__ == '__main__':
    inspect()
