import sqlite3
import pandas as pd

conn = sqlite3.connect("cronograma_inteligente.db")
print("=== FIRST 20 CRONOGRAMAS ===")
print(pd.read_sql_query("""
    SELECT id, fecha_inicio, fecha_fin, notas, estado FROM cronogramas 
    WHERE fecha_inicio >= '2026-01-01' AND fecha_fin <= '2026-06-30'
    ORDER BY fecha_inicio LIMIT 20
""", conn))
print("\n=== LAST 20 CRONOGRAMAS ===")
print(pd.read_sql_query("""
    SELECT id, fecha_inicio, fecha_fin, notas, estado FROM cronogramas 
    WHERE fecha_inicio >= '2026-01-01' AND fecha_fin <= '2026-06-30'
    ORDER BY fecha_inicio DESC LIMIT 20
""", conn))
conn.close()
