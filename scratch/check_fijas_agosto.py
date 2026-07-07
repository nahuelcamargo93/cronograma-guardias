import sqlite3
import pandas as pd

conn = sqlite3.connect('cronograma_inteligente.db')

print("=== Asignaciones Fijas Activas ===")
try:
    df_fijas = pd.read_sql_query("""
        SELECT personal_nombre, fecha, dia_semana, turno, activo
        FROM personal_asignaciones_fijas
        WHERE activo = 1
    """, conn)
    print(df_fijas)
except Exception as e:
    print(f"Error al leer personal_asignaciones_fijas: {e}")

print("\n=== Asignaciones Fijas del Servicio 2 en Agosto ===")
try:
    df_fijas_s2 = pd.read_sql_query("""
        SELECT af.personal_nombre, af.fecha, af.dia_semana, af.turno
        FROM personal_asignaciones_fijas af
        JOIN personal p ON af.personal_nombre = p.nombre
        WHERE p.servicio_id = 2 AND af.activo = 1
          AND (af.fecha IS NULL OR (af.fecha >= '2026-08-01' AND af.fecha <= '2026-08-31'))
    """, conn)
    print(df_fijas_s2)
    print(f"Total asignaciones fijas servicio 2 en agosto: {len(df_fijas_s2)}")
except Exception as e:
    print(f"Error: {e}")

conn.close()
