import sqlite3
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import get_connection

def inspect():
    conn = get_connection()
    res = conn.execute("""
        SELECT dc.id, p.nombre, dc.tipo_dia, dc.hora_inicio, dc.hora_fin, dc.cantidad_min, dc.cantidad_max, dc.dias_semana, dc.activo
        FROM demanda_config dc
        JOIN puestos p ON dc.puesto_id = p.id
        WHERE p.servicio_id = 4
    """).fetchall()
    
    print("=== DEMANDA CONFIG DIAS_SEMANA ===")
    for row in res:
        print(f"ID: {row[0]} | Puesto: {row[1]:<12} | Tipo: {row[2]:<15} | Slot: {row[3]} - {row[4]} | Min: {row[5]} | Max: {row[6]} | Dias: {row[7]!r} | Activo: {row[8]}")

if __name__ == "__main__":
    inspect()
