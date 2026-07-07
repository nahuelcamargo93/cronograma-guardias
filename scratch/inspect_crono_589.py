import sqlite3
import pandas as pd

conn = sqlite3.connect("cronograma_inteligente.db")
print("=== Ultimos 5 Cronogramas ===")
df_c = pd.read_sql_query("SELECT id, fecha_inicio, fecha_fin, creado_en, estado, servicio_id FROM cronogramas ORDER BY id DESC LIMIT 5", conn)
print(df_c)

print("\n=== Ultimos 10 FLR Asignados en la DB ===")
df_flr = pd.read_sql_query("SELECT * FROM flr_asignados ORDER BY id DESC LIMIT 10", conn)
print(df_flr)

conn.close()
