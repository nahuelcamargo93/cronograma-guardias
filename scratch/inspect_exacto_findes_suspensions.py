import sqlite3
import pandas as pd

conn = sqlite3.connect("cronograma_inteligente.db")
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', 1000)

print("=== EXACTO_FINDES_MES suspensions in personal_reglas_ajustes for June 2026 ===")
df = pd.read_sql_query("""
    SELECT id, personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, activo 
    FROM personal_reglas_ajustes 
    WHERE codigo_regla = 'EXACTO_FINDES_MES' 
      AND fecha_inicio <= '2026-06-30' 
      AND fecha_fin >= '2026-06-01'
""", conn)
print(df)
conn.close()
