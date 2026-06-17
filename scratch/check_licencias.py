import sqlite3
import pandas as pd

conn = sqlite3.connect('cronograma_inteligente.db')

print("=== LICENCIAS EN JULIO 2026 (SERVICIO 3) ===")
df_lic = pd.read_sql_query("""
    SELECT l.nombre, l.tipo, l.fecha_inicio, l.fecha_fin, l.activa
    FROM licencias l
    JOIN personal p ON l.nombre = p.nombre
    WHERE p.servicio_id = 3 AND l.fecha_inicio <= '2026-07-31' AND l.fecha_fin >= '2026-07-01'
    ORDER BY l.fecha_inicio, l.nombre
""", conn)
print(df_lic)

conn.close()
