import sqlite3
import pandas as pd

conn = sqlite3.connect("cronograma_inteligente.db")
print("=== GUARDIAS FOR ENFERMERIA UTI (servicio_id = 2) IN DB ===")
print(pd.read_sql_query("""
    SELECT c.id as cronograma_id, c.fecha_inicio, c.fecha_fin, c.estado, COUNT(*) as cantidad
    FROM guardias g
    JOIN cronogramas c ON g.cronograma_id = c.id
    JOIN personal p ON g.nombre = p.nombre
    WHERE p.servicio_id = 2
    GROUP BY c.id, c.fecha_inicio, c.fecha_fin, c.estado
""", conn))
conn.close()
