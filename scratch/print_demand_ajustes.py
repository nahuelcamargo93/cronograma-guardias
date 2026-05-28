import sqlite3
import pandas as pd

conn = sqlite3.connect("cronograma_inteligente.db")
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', 1000)

query = """
    SELECT da.id, da.fecha_inicio, da.fecha_fin, da.cantidad_min, da.cantidad_max, da.operador, da.activo, 
           dc.tipo_dia, p.nombre as puesto_nombre
    FROM demanda_ajustes da
    JOIN demanda_config dc ON da.demanda_config_id = dc.id
    JOIN puestos p ON dc.puesto_id = p.id
    WHERE p.servicio_id = 3
      AND da.fecha_inicio <= '2026-06-30'
      AND da.fecha_fin >= '2026-06-01'
"""
df = pd.read_sql_query(query, conn)
print("=== DEMANDA_AJUSTES FOR JUNE 2026 ===")
print(df)
conn.close()
