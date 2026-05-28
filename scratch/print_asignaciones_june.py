import sqlite3
import pandas as pd

conn = sqlite3.connect("cronograma_inteligente.db")
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', 1000)

print("=== personal_reglas FOR ASIGNACION_FIJA ===")
df_rules = pd.read_sql_query("SELECT * FROM personal_reglas WHERE codigo_regla = 'ASIGNACION_FIJA'", conn)
print(df_rules)

print("\n=== personal_reglas_ajustes FOR ASIGNACION_FIJA ===")
df_ajustes = pd.read_sql_query("""
    SELECT * 
    FROM personal_reglas_ajustes 
    WHERE codigo_regla = 'ASIGNACION_FIJA' 
      AND fecha_inicio <= '2026-06-30' 
      AND fecha_fin >= '2026-06-01'
""", conn)
print(df_ajustes)

conn.close()
