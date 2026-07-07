import sqlite3
import pandas as pd

conn = sqlite3.connect('cronograma_inteligente.db')

print("\n=== LICENCIAS DE CARRERAS FLAVIA EN AGOSTO 2026 ===")
df_lic = pd.read_sql_query("""
    SELECT fecha_inicio, fecha_fin, tipo, activa FROM licencias 
    WHERE nombre = 'CARRERAS FLAVIA' 
      AND fecha_inicio <= '2026-08-31' 
      AND fecha_fin >= '2026-08-01'
""", conn)
print(df_lic)

print("\n=== GUARDIAS DETALLADAS EN CRONOGRAMA 583 (JULIO 2026) ===")
df_g = pd.read_sql_query("""
    SELECT fecha, turno, horas, es_finde 
    FROM guardias 
    WHERE nombre = 'CARRERAS FLAVIA' AND cronograma_id = 583 
    ORDER BY fecha
""", conn)
print(df_g.to_string())

conn.close()
