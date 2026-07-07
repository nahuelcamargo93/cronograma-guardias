import sqlite3
import pandas as pd

conn = sqlite3.connect("cronograma_inteligente.db")
print("=== Enfermeros que trabajaron el 31 de Julio de 2026 en Crono 583 ===")
df = pd.read_sql_query("""
    SELECT nombre, turno, horas 
    FROM guardias 
    WHERE cronograma_id = 583 AND fecha = '2026-07-31'
    ORDER BY nombre
""", conn)
print(df)
conn.close()
