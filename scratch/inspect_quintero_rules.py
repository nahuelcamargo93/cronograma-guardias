import sqlite3
import pandas as pd

conn = sqlite3.connect("cronograma_inteligente.db")
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', 1000)

print("=== personal_reglas FOR Quintero Anabela Belen ===")
df_rules = pd.read_sql_query("""
    SELECT * 
    FROM personal_reglas 
    WHERE personal_nombre LIKE '%Quintero%'
""", conn)
print(df_rules)

print("\n=== personal_reglas_ajustes FOR Quintero Anabela Belen ===")
df_ajustes = pd.read_sql_query("""
    SELECT * 
    FROM personal_reglas_ajustes 
    WHERE personal_nombre LIKE '%Quintero%'
""", conn)
print(df_ajustes)

conn.close()
