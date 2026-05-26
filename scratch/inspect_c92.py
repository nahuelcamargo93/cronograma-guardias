import sqlite3
import pandas as pd

conn = sqlite3.connect("cronograma_inteligente.db")
print("=== CRONOGRAMA 92 INFO ===")
print(conn.execute("SELECT * FROM cronogramas WHERE id = 92").fetchone())
print("\n=== GUARDIAS IN CRONOGRAMA 92 BY SERVICE ===")
print(pd.read_sql_query("""
    SELECT s.nombre as servicio, COUNT(*) as cantidad
    FROM guardias g
    JOIN personal p ON g.nombre = p.nombre
    LEFT JOIN servicios s ON p.servicio_id = s.id
    WHERE g.cronograma_id = 92
    GROUP BY s.nombre
""", conn))
conn.close()
