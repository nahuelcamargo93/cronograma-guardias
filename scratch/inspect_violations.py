import sqlite3
import pandas as pd

conn = sqlite3.connect('cronograma_inteligente.db')

print("=== INFRACCIONES DEL CRONOGRAMA 586 (MODO DEBUG SOFT) ===")
df_viol = pd.read_sql_query("""
    SELECT codigo_regla, detalle 
    FROM infracciones_debug 
    WHERE cronograma_id = 586
""", conn)
print(df_viol.to_string())

conn.close()
