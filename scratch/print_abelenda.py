import sqlite3
import pandas as pd

conn = sqlite3.connect('cronograma_inteligente.db')
query = """
    SELECT g.fecha, g.turno, g.horas, g.es_finde
    FROM guardias g
    WHERE g.nombre = 'ABELENDA GRISELL'
      AND g.cronograma_id = (SELECT MAX(cronograma_id) FROM guardias)
    ORDER BY g.fecha
"""
df = pd.read_sql_query(query, conn)
conn.close()
print("=== ABELENDA GRISELL July 2026 shifts ===")
print(df.to_string())
