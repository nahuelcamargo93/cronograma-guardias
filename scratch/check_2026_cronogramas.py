import sqlite3
import pandas as pd

conn = sqlite3.connect("cronograma_inteligente.db")
print("=== CRONOGRAMAS IN DATABASE FOR 2026 ===")
df = pd.read_sql_query("SELECT * FROM cronogramas WHERE fecha_inicio LIKE '2026%' OR fecha_fin LIKE '2026%'", conn)
print(df)
conn.close()
