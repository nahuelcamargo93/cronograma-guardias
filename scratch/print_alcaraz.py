import sqlite3
import pandas as pd

conn = sqlite3.connect('cronograma_inteligente.db')
query = """
    SELECT fecha, turno
    FROM guardias
    WHERE nombre = 'MEDINA LAURA'
      AND cronograma_id = (SELECT MAX(cronograma_id) FROM guardias)
    ORDER BY fecha
"""
df = pd.read_sql_query(query, conn)
print(df)
conn.close()
