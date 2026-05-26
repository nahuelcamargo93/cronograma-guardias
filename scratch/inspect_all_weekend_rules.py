import sqlite3
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import get_connection

def inspect():
    conn = get_connection()
    print("--- WEEKEND RULES IN SERVICIOS_REGLAS ---")
    rows = conn.execute("""
        SELECT sr.servicio_id, s.nombre, sr.codigo_regla, sr.parametros_json, sr.activo 
        FROM servicios_reglas sr
        JOIN servicios s ON sr.servicio_id = s.id
        WHERE sr.codigo_regla LIKE '%FINDE%' OR sr.codigo_regla LIKE '%FINDES%'
    """).fetchall()
    for r in rows:
        print(f"ServID: {r[0]} ({r[1]}), Rule: {r[2]}, Active: {r[4]}")
        print(f"  Params: {r[3]}")

if __name__ == "__main__":
    inspect()
