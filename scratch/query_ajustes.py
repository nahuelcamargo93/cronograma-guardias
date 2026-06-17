import sqlite3
import pandas as pd

conn = sqlite3.connect("cronograma_inteligente.db")
query = "SELECT * FROM personal_reglas_ajustes WHERE id IN (1780, 1781, 1782)"
df = pd.read_sql_query(query, conn)
print(df.to_string())
conn.close()
