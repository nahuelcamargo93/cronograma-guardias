import sqlite3
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import get_connection

def inspect():
    conn = get_connection()
    res = conn.execute("""
        SELECT p.nombre, p.categoria, p.rol, pr.parametros_json 
        FROM personal p
        LEFT JOIN personal_reglas pr ON p.nombre = pr.personal_nombre AND pr.codigo_regla = 'EXCLUIR_TURNOS'
        WHERE p.servicio_id = 4
        ORDER BY p.categoria, p.nombre
    """).fetchall()
    
    print("=== EXCLUSIONES DE TURNO POR PERSONAL EN SERVICIO 4 ===")
    for row in res:
        print(f"Name: {row[0]:<35} | Cat: {row[1]} | Rol: {row[2]:<20} | Excluidos: {row[3]}")

if __name__ == "__main__":
    inspect()
