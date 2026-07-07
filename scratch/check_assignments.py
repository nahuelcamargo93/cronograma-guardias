import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sqlite3
conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

# Find last cronograma for service_id = 4
row = cursor.execute("""
    SELECT c.id, c.fecha_inicio, c.fecha_fin, c.notas
    FROM cronogramas c
    JOIN guardias g ON c.id = g.cronograma_id
    JOIN personal p ON g.nombre = p.nombre
    WHERE p.servicio_id = 4
    ORDER BY c.id DESC
    LIMIT 1
""").fetchone()

if row:
    crono_id, fecha_inicio, fecha_fin, notas = row
    print(f"Last cronograma ID {crono_id} ({fecha_inicio} to {fecha_fin}) - {notas}")
    
    # Query guardias assigned to the 4 persons
    guardias = cursor.execute("""
        SELECT nombre, fecha, turno
        FROM guardias
        WHERE cronograma_id = ? AND nombre IN (
            'FERNANDEZ Claudia Elizabeth', 
            'QUINTANA Felipe Gabriel', 
            'SUÑER Mara Tatiana', 
            'BRIZUELA Irma'
        )
        ORDER BY nombre, fecha
    """, (crono_id,)).fetchall()
    
    print("\nGuardias for the 4 persons:")
    for g in guardias:
        print(g)
else:
    print("No cronograma found for service 4.")
conn.close()
