import sqlite3
import pandas as pd

conn = sqlite3.connect("cronograma_inteligente.db")

print("=== TOTAL HOURS ASSIGNED IN CRONOGRAMA 216 ===")
query = """
    SELECT g.nombre, p.rol, COUNT(*) as shift_count, SUM(tc.horas) as total_horas
    FROM guardias g
    JOIN personal p ON g.nombre = p.nombre
    JOIN turnos_config tc ON g.turno = tc.nombre AND tc.servicio_id = 3
    WHERE g.cronograma_id = 216
    GROUP BY g.nombre, p.rol
    ORDER BY p.rol, total_horas DESC
"""
df = pd.read_sql_query(query, conn)
print(df)

print(f"\nSum of hours assigned to Planta in Cronograma 216: {df[df['rol'] == 'Planta']['total_horas'].sum()} hs")
print(f"Sum of hours assigned to Residente in Cronograma 216: {df[df['rol'] == 'Residente']['total_horas'].sum()} hs")

conn.close()
