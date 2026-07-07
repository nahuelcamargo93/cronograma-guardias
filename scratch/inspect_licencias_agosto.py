import sqlite3
import pandas as pd

conn = sqlite3.connect('cronograma_inteligente.db')

print("=== LICENCIAS EN AGOSTO 2026 ===")
df_lic = pd.read_sql_query("""
    SELECT l.nombre, l.tipo, l.fecha_inicio, l.fecha_fin, p.servicio_id
    FROM licencias l
    JOIN personal p ON l.nombre = p.nombre
    WHERE p.servicio_id = 2 
      AND l.fecha_inicio <= '2026-08-31' 
      AND l.fecha_fin >= '2026-08-01'
""", conn)
print(df_lic)

conn.close()
