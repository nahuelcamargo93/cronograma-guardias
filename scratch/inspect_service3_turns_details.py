import sqlite3
import pandas as pd

conn = sqlite3.connect("cronograma_inteligente.db")
print("=== TURNOS CONFIG FOR SERVICIO 3 ===")
df = pd.read_sql_query("SELECT nombre, horas, hora_inicio FROM turnos_config WHERE servicio_id = 3", conn)
print(df)
conn.close()
