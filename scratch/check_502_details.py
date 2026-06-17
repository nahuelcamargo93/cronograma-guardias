import sqlite3
import pandas as pd

conn = sqlite3.connect('cronograma_inteligente.db')

print("=== DISTRIBUCION DE HORAS POR EMPLEADO EN ID 502 ===")
df = pd.read_sql_query("""
    SELECT nombre, SUM(horas) as total_horas, COUNT(*) as turnos_totales
    FROM guardias
    WHERE cronograma_id = 502
    GROUP BY nombre
    ORDER BY total_horas DESC
""", conn)
print(df)

print("\n=== DETALLE DE GUARDIAS EN LOS PRIMEROS 5 DIAS DE JULIO EN ID 502 ===")
df_days = pd.read_sql_query("""
    SELECT fecha, turno, nombre
    FROM guardias
    WHERE cronograma_id = 502 AND fecha <= '2026-07-05'
    ORDER BY fecha, turno
""", conn)
print(df_days.to_string())

conn.close()
