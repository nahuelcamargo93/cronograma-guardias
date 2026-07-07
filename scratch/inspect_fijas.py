import sqlite3
import pandas as pd

conn = sqlite3.connect('cronograma_inteligente.db')

print("=== ASIGNACIONES FIJAS EN AGOSTO 2026 ===")
df_fijas = pd.read_sql_query("""
    SELECT personal_nombre, fecha, dia_semana, turno, activo 
    FROM personal_asignaciones_fijas
    WHERE activo = 1 AND personal_nombre IN (
        SELECT nombre FROM personal WHERE servicio_id = 2
    )
""", conn)
print(df_fijas)

conn.close()
