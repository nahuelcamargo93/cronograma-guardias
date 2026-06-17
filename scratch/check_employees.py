import sqlite3
import pandas as pd

conn = sqlite3.connect('cronograma_inteligente.db')

print("=== EMPLEADOS SERVICIO 3 ===")
df_emp = pd.read_sql_query("""
    SELECT nombre, categoria, rol, activo, servicio_id
    FROM personal
    WHERE servicio_id = 3 AND COALESCE(activo, 1) = 1
""", conn)
print(df_emp)
print("Total active employees:", len(df_emp))

print("\n=== PUESTOS HABILITADOS POR EMPLEADO ===")
df_puestos = pd.read_sql_query("""
    SELECT pp.personal_nombre, p.nombre as puesto, pp.es_primario
    FROM personal_puestos pp
    JOIN puestos p ON pp.puesto_id = p.id
    WHERE p.servicio_id = 3
    ORDER BY pp.personal_nombre
""", conn)
print(df_puestos)

conn.close()
