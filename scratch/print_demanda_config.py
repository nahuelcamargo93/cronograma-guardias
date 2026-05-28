import sqlite3
import pandas as pd

conn = sqlite3.connect("cronograma_inteligente.db")
print("=== DEMANDA_CONFIG FOR SERVICE 3 ===")
df = pd.read_sql_query("""
    SELECT dc.*, p.nombre as puesto_nombre 
    FROM demanda_config dc
    JOIN puestos p ON dc.puesto_id = p.id
    WHERE p.servicio_id = 3
""", conn)
print(df)
conn.close()
