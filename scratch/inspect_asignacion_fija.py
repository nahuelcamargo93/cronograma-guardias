import sqlite3
import pandas as pd

conn = sqlite3.connect("cronograma_inteligente.db")
print("=== personal_reglas FOR ASIGNACION_FIJA ===")
print(pd.read_sql_query("SELECT * FROM personal_reglas WHERE codigo_regla = 'ASIGNACION_FIJA'", conn))

print("\n=== personal_reglas_ajustes FOR ASIGNACION_FIJA ===")
print(pd.read_sql_query("SELECT * FROM personal_reglas_ajustes WHERE codigo_regla = 'ASIGNACION_FIJA'", conn))
conn.close()
