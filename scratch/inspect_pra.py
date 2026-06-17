import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.connection import get_connection

def inspect():
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT id, personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo 
            FROM personal_reglas_ajustes 
            WHERE servicio_id = 2 AND codigo_regla = 'FRANCO_FORZADO'
              AND (fecha_inicio <= '2026-07-31' AND fecha_fin >= '2026-07-01')
        """).fetchall()
        
        print(f"Se encontraron {len(rows)} francos forzados para el servicio 2 en julio 2026:")
        for r in rows:
            print(f"  ID: {r[0]} | Nombre: {r[1]} | Regla: {r[2]} | Rango: {r[3]} a {r[4]} | Accion: {r[5]} | Parámetros: {r[6]} | Activo: {r[7]}")

if __name__ == "__main__":
    inspect()
