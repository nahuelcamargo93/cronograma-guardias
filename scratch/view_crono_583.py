import sqlite3
import pandas as pd

conn = sqlite3.connect('cronograma_inteligente.db')

print("=== Cronogramas guardados ===")
df_cronos = pd.read_sql_query("SELECT id, servicio_id, fecha_inicio, fecha_fin, estado, notas FROM cronogramas ORDER BY id DESC LIMIT 10", conn)
print(df_cronos)

print("\n=== Detalle del Cronograma 583 (o el último del servicio 2) ===")
print("\n=== Reglas activas para el Servicio 2 ===")
df_reglas = pd.read_sql_query("""
    SELECT codigo_regla, parametros_json, activo
    FROM servicios_reglas
    WHERE servicio_id = 2
""", conn)
print(df_reglas)

print("\n=== Reglas de personal activas ===")
df_reglas_emp = pd.read_sql_query("""
    SELECT personal_nombre, codigo_regla, parametros_json
    FROM personal_reglas
    WHERE activo = 1 AND personal_nombre IN (
        SELECT nombre FROM personal WHERE servicio_id = 2
    )
""", conn)
print(df_reglas_emp)

conn.close()
