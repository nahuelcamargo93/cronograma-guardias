import sqlite3
import pandas as pd

conn = sqlite3.connect("cronograma_inteligente.db")
query = """
    SELECT g.fecha, g.turno, COUNT(*) as qty, tc.horas
    FROM guardias g
    JOIN turnos_config tc ON g.turno = tc.nombre AND tc.servicio_id = 3
    WHERE g.cronograma_id = 216
    GROUP BY g.fecha, g.turno
    ORDER BY g.fecha, g.turno
"""
df = pd.read_sql_query(query, conn)
print(df.head(20))
print("\nTurno type totals:")
print(df.groupby('turno')['qty'].sum())
print("\nGrand total hours assigned in 216:", (df['qty'] * df['horas']).sum())
conn.close()
