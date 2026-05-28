import sqlite3
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import get_connection

def inspect():
    conn = get_connection()
    print("=== DEMANDA CONFIG (Servicio 3) ===")
    res = conn.execute("""
        SELECT dc.id, p.nombre, dc.tipo_dia, dc.hora_inicio, dc.hora_fin, dc.cantidad_min, dc.cantidad_max, dc.activo
        FROM demanda_config dc
        JOIN puestos p ON dc.puesto_id = p.id
        WHERE p.servicio_id = 3
    """).fetchall()
    for row in res:
        print(f"ID: {row[0]} | Puesto: {row[1]:<12} | Tipo: {row[2]:<15} | Slot: {row[3]} - {row[4]} | Min: {row[5]} | Max: {row[6]} | Activo: {row[7]}")
        
    print("\n=== DEMANDA AJUSTES (Servicio 3) ===")
    res = conn.execute("""
        SELECT da.fecha_inicio, da.fecha_fin, p.nombre, da.cantidad_min, da.cantidad_max, da.activo, da.dias_semana, da.id
        FROM demanda_ajustes da
        JOIN demanda_config dc ON da.demanda_config_id = dc.id
        JOIN puestos p ON dc.puesto_id = p.id
        WHERE p.servicio_id = 3
    """).fetchall()
    for row in res:
        print(f"ID: {row[7]} | Range: {row[0]} to {row[1]} | Puesto: {row[2]:<12} | Min: {row[3]} | Max: {row[4]} | Activo: {row[5]} | Dias: {row[6]}")

if __name__ == "__main__":
    inspect()
