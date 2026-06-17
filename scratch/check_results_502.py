import sqlite3
import pandas as pd

conn = sqlite3.connect('cronograma_inteligente.db')

print("=== INFRACCIONES FOR ID 502 ===")
df = pd.read_sql_query("SELECT * FROM infracciones_debug WHERE cronograma_id = 502", conn)
print(df)

conn.close()
