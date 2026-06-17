import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else '.'
project_root = os.path.abspath(os.path.join(script_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from database.connection import get_connection

def inspect():
    with get_connection() as conn:
        print("=== SERVICIOS ===")
        rows = conn.execute("SELECT id, nombre FROM servicios").fetchall()
        for r in rows:
            print(f"ID: {r[0]}, Nombre: {r[1]}")
            
        print("\n=== TURNOS CONFIG SERVICIO 2 ===")
        rows = conn.execute("SELECT id, nombre, hora_inicio, horas, dias_semana, activo FROM turnos_config WHERE servicio_id = 2").fetchall()
        for r in rows:
            print(f"ID: {r[0]}, Nombre: {r[1]}, Inicio: {r[2]}, Horas: {r[3]}, Dias: {r[4]}, Activo: {r[5]}")

        print("\n=== PERSONAL SERVICIO 2 ===")
        rows = conn.execute("SELECT nombre, categoria, rol, activo FROM personal WHERE servicio_id = 2").fetchall()
        for r in rows:
            print(f"Nombre: {r[0]}, Cat: {r[1]}, Rol: {r[2]}, Activo: {r[3]}")

        print("\n=== REGLAS SERVICIO 2 ===")
        rows = conn.execute("SELECT codigo_regla, parametros_json, activo FROM servicios_reglas WHERE servicio_id = 2").fetchall()
        for r in rows:
            print(f"Regla: {r[0]}, Activo: {r[2]}, Params: {r[1]}")

        print("\n=== REGLAS PERSONAL SERVICIO 2 ===")
        rows = conn.execute("""
            SELECT pr.personal_nombre, pr.codigo_regla, pr.parametros_json, pr.activo 
            FROM personal_reglas pr
            JOIN personal p ON pr.personal_nombre = p.nombre
            WHERE p.servicio_id = 2
        """).fetchall()
        for r in rows:
            print(f"Nombre: {r[0]}, Regla: {r[1]}, Activo: {r[3]}, Params: {r[2]}")

if __name__ == '__main__':
    inspect()
