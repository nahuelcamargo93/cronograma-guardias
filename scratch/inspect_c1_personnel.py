import sqlite3
import pandas as pd

conn = sqlite3.connect("cronograma_inteligente.db")
print("=== GUARDIAS IN CRONOGRAMA 1 BY SERVICE ===")
print(pd.read_sql_query("""
    SELECT s.nombre as servicio, COUNT(*) as cantidad_guardias
    FROM guardias g
    JOIN personal p ON g.nombre = p.nombre
    LEFT JOIN servicios s ON p.servicio_id = s.id
    WHERE g.cronograma_id = 1
    GROUP BY s.nombre
""", conn))
conn.close()
