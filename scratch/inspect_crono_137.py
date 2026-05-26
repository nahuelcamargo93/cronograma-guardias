import sqlite3
import pandas as pd

conn = sqlite3.connect("cronograma_inteligente.db")

print("--- DETAILS OF CRONOGRAMA 137 ---")
df_crono = pd.read_sql_query("SELECT id, fecha_inicio, fecha_fin, estado, notas FROM cronogramas WHERE id = 137", conn)
print(df_crono)

print("\n--- GUARDIAS OF CRONOGRAMA 137 ---")
df_guardias = pd.read_sql_query("""
    SELECT g.id, g.nombre, g.fecha, g.turno, g.horas
    FROM guardias g
    WHERE g.cronograma_id = 137
""", conn)
print(df_guardias)

conn.close()
