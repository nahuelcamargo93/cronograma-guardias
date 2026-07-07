import sqlite3
import pandas as pd

conn = sqlite3.connect("cronograma_inteligente.db")
print("=== Todos los FLR del Cronograma 589 ===")
df_flr = pd.read_sql_query("""
    SELECT id, nombre, fecha_inicio, fecha_fin 
    FROM flr_asignados 
    WHERE cronograma_id = 589 
    ORDER BY fecha_inicio, nombre
""", conn)
print(df_flr)

print("\n=== FLR que inician el 1 de Agosto ===")
print(df_flr[df_flr['fecha_inicio'] == '2026-08-01'])

conn.close()
