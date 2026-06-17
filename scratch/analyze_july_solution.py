import sqlite3
import pandas as pd

conn = sqlite3.connect('cronograma_inteligente.db')

print("=== Guardias del Cronograma 499 (Debug Soft) - Primera Semana de Julio ===")
query = """
    SELECT fecha, turno, nombre 
    FROM guardias 
    WHERE cronograma_id = 499 AND fecha BETWEEN '2026-07-01' AND '2026-07-07'
    ORDER BY fecha, turno, nombre
"""
df = pd.read_sql_query(query, conn)
pd.set_option('display.max_rows', 100)
print(df)

print("\n=== Infracciones detalladas para el Cronograma 499 ===")
infracciones_df = pd.read_sql_query("SELECT codigo_regla, detalle FROM infracciones_debug WHERE cronograma_id = 499", conn)
print(infracciones_df)

conn.close()
