import sqlite3
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import get_connection

def inspect():
    conn = get_connection()
    
    # 1. Find all cronogramas for servicio_id = 4
    cronogramas = conn.execute("""
        SELECT c.id, c.fecha_inicio, c.fecha_fin, c.creado_en, c.notas, c.estado
        FROM cronogramas c
        JOIN guardias g ON c.id = g.cronograma_id
        JOIN personal p ON g.nombre = p.nombre
        WHERE p.servicio_id = 4
        GROUP BY c.id
        ORDER BY c.id DESC
    """).fetchall()
    
    print("=== CRONOGRAMAS FOR SERVICIO 4 ===")
    if not cronogramas:
        print("No historical cronogramas found containing Servicio 4 guardias.")
        return
        
    for cr in cronogramas:
        print(f"ID: {cr[0]} | Rango: {cr[1]} to {cr[2]} | Creado: {cr[3]} | Notas: {cr[4]} | Estado: {cr[5]}")
        
    # Check guardias of the latest one
    latest_id = cronogramas[0][0]
    res = conn.execute("""
        SELECT g.fecha, g.turno, g.nombre 
        FROM guardias g
        WHERE g.cronograma_id = ? AND g.turno LIKE '%Supervisor%'
        ORDER BY g.fecha, g.turno
    """, (latest_id,)).fetchall()
    
    print(f"\n=== SUPERVISOR SHIFTS IN LATEST CRONOGRAMA ID {latest_id} FOR SERVICIO 4 ===")
    for row in res:
        print(f"Fecha: {row[0]} | Turno: {row[1]:<20} | Nombre: {row[2]}")

if __name__ == "__main__":
    inspect()
