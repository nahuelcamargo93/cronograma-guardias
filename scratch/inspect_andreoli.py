import sqlite3
import pandas as pd

conn = sqlite3.connect("cronograma_inteligente.db")
print("=== Guardias de ANDREOLI LUCIANA en Cronograma 589 ===")
df_g = pd.read_sql_query("""
    SELECT fecha, turno, horas 
    FROM guardias 
    WHERE cronograma_id = 589 AND nombre = 'ANDREOLI LUCIANA'
    ORDER BY fecha
""", conn)
print(df_g)

print("\n=== FLR asignados a ANDREOLI LUCIANA en Cronograma 589 ===")
df_flr = pd.read_sql_query("""
    SELECT * FROM flr_asignados 
    WHERE cronograma_id = 589 AND nombre = 'ANDREOLI LUCIANA'
""", conn)
print(df_flr)

conn.close()
