import sqlite3
import pandas as pd

conn = sqlite3.connect("cronograma_inteligente.db")
print("=== ALL UNIQUE SHIFT NAMES IN GUARDIAS TABLE ===")
print(pd.read_sql_query("SELECT DISTINCT turno FROM guardias ORDER BY turno", conn))
conn.close()
