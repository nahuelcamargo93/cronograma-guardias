import sqlite3
import pandas as pd

conn = sqlite3.connect("cronograma_inteligente.db")
print("=== ESCUDERO / LUCERO IN DATABASE ===")
print(pd.read_sql_query("SELECT nombre, rol, categoria, servicio_id FROM personal WHERE nombre LIKE '%ESCUDERO%' OR nombre LIKE '%LUCERO%'", conn))
conn.close()
