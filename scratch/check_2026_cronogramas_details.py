import sqlite3
import pandas as pd

conn = sqlite3.connect("cronograma_inteligente.db")
print("=== CRONOGRAMAS BETWEEN 2026-01-01 AND 2026-06-30 ===")
df = pd.read_sql_query("""
    SELECT * FROM cronogramas 
    WHERE fecha_inicio >= '2026-01-01' AND fecha_fin <= '2026-06-30'
    ORDER BY fecha_inicio
""", conn)
print(df)
conn.close()
