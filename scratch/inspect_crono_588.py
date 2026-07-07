import sqlite3
import pandas as pd

conn = sqlite3.connect("cronograma_inteligente.db")
print("=== Cronograma 588 ===")
df_c = pd.read_sql_query("SELECT * FROM cronogramas WHERE id = 588", conn)
print(df_c)

print("\n=== Guardias del Cronograma 588 en la franja del 1 al 4 de agosto ===")
df_g = pd.read_sql_query("""
    SELECT g.nombre, g.fecha, g.turno, g.horas, p.rol
    FROM guardias g
    JOIN personal p ON g.nombre = p.nombre
    WHERE g.cronograma_id = 588 AND g.fecha BETWEEN '2026-08-01' AND '2026-08-04'
    ORDER BY g.fecha, g.nombre
""", conn)
print(df_g)

print("\n=== FLR asignados en el Cronograma 588 ===")
df_flr = pd.read_sql_query("SELECT * FROM flr_asignados WHERE cronograma_id = 588", conn)
print(df_flr)

conn.close()
