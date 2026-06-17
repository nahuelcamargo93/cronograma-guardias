import sqlite3
import pandas as pd

conn = sqlite3.connect('cronograma_inteligente.db')

crono_id = 309

print("=== HORAS ASIGNADAS EN CRONOGRAMA 309 ===")
df_h = pd.read_sql_query("""
    SELECT nombre, SUM(horas) as horas_totales
    FROM guardias
    WHERE cronograma_id = ?
    GROUP BY nombre
    ORDER BY horas_totales DESC
""", conn, params=(crono_id,))
print(df_h)

conn.close()
