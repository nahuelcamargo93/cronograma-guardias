import sqlite3
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import get_connection

def inspect():
    conn = get_connection()
    res = conn.execute("""
        SELECT pra.personal_nombre, p.categoria, pra.codigo_regla, pra.fecha_inicio, pra.fecha_fin, pra.accion, pra.parametros_json, pra.activo
        FROM personal_reglas_ajustes pra
        JOIN personal p ON pra.personal_nombre = p.nombre
        WHERE p.servicio_id = 4 AND pra.fecha_inicio <= '2026-06-30' AND pra.fecha_fin >= '2026-06-01'
        ORDER BY pra.personal_nombre, pra.codigo_regla
    """).fetchall()
    
    print("=== PERSONAL RULES ADJUSTMENTS FOR JUNE 2026 ===")
    for row in res:
        print(f"Name: {row[0]:<30} | Cat: {row[1]} | Rule: {row[2]:<25} | Range: {row[3]} to {row[4]} | Accion: {row[5]} | Params: {row[6]} | Activo: {row[7]}")

if __name__ == "__main__":
    inspect()
