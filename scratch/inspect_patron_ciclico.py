import sqlite3
import pandas as pd

conn = sqlite3.connect("cronograma_inteligente.db")
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', 1000)

print("=== PATRON_CICLICO in personal_reglas ===")
print(pd.read_sql_query("SELECT * FROM personal_reglas WHERE codigo_regla = 'PATRON_CICLICO'", conn))

print("\n=== PATRON_CICLICO in personal_reglas_ajustes ===")
print(pd.read_sql_query("SELECT * FROM personal_reglas_ajustes WHERE codigo_regla = 'PATRON_CICLICO'", conn))

conn.close()
