import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sqlite3
import pandas as pd

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

# Get all personal for service 4
personal = cursor.execute("""
    SELECT nombre, categoria, rol FROM personal 
    WHERE servicio_id = 4 AND COALESCE(activo, 1) = 1
    ORDER BY categoria, nombre
""").fetchall()

print("All active personnel for service 4:")
print(f"{'Nombre':<30} | {'Categoria':<10} | {'Rol':<20}")
print("-" * 68)
for p in personal:
    print(f"{p[0]:<30} | {p[1]:<10} | {p[2]:<20}")

# Get last cronograma ID
row = cursor.execute("""
    SELECT c.id FROM cronogramas c
    JOIN guardias g ON c.id = g.cronograma_id
    JOIN personal p ON g.nombre = p.nombre
    WHERE p.servicio_id = 4
    ORDER BY c.id DESC
    LIMIT 1
""").fetchone()

if row:
    crono_id = row[0]
    # For each person, list distinct turnos assigned in this cronograma
    print("\nDistinct assigned turnos in latest cronograma:")
    print(f"{'Nombre':<30} | {'Turnos asignados'}")
    print("-" * 55)
    for p in personal:
        name = p[0]
        turnos = cursor.execute("""
            SELECT DISTINCT turno FROM guardias
            WHERE cronograma_id = ? AND nombre = ?
        """, (crono_id, name)).fetchall()
        turnos_str = ", ".join(t[0] for t in turnos)
        print(f"{name:<30} | {turnos_str}")
        
conn.close()
