import sqlite3
import pandas as pd

conn = sqlite3.connect("cronograma_inteligente.db")
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', 1000)

print("=== reglas_servicio FOR SERVICE 3 ===")
df = pd.read_sql_query("SELECT * FROM reglas_servicio WHERE servicio_id = 3", conn)
print(df)
conn.close()
