import sqlite3
import pandas as pd

conn = sqlite3.connect("cronograma_inteligente.db")
print("=== Reglas individuales de MANEJO_FINDES ===")
df = pd.read_sql_query("""
    SELECT personal_nombre, codigo_regla, parametros_json, activo 
    FROM personal_reglas 
    WHERE codigo_regla = 'MANEJO_FINDES'
""", conn)
print(df)

print("\n=== Ajustes temporales de MANEJO_FINDES ===")
df_a = pd.read_sql_query("""
    SELECT personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo 
    FROM personal_reglas_ajustes 
    WHERE codigo_regla = 'MANEJO_FINDES'
""", conn)
print(df_a)

conn.close()
