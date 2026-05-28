import sqlite3
import pandas as pd

conn = sqlite3.connect("cronograma_inteligente.db")
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', 1000)

query = """
    SELECT pp.personal_nombre, p.nombre as puesto_nombre, pp.es_primario
    FROM personal_puestos pp
    JOIN puestos p ON pp.puesto_id = p.id
    WHERE p.servicio_id = 3
"""
df = pd.read_sql_query(query, conn)
print(df)
conn.close()
