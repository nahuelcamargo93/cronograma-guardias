import sqlite3
import pandas as pd

conn = sqlite3.connect('cronograma_inteligente.db')
pd.set_option('display.max_columns', None)
pd.set_option('display.max_colwidth', None)

print("=== PERSONAL SERVICIO 1 ===")
df_p = pd.read_sql_query("""
    SELECT nombre, rol, activo
    FROM personal 
    WHERE servicio_id = 1
""", conn)
print(df_p)

print("\n=== PUESTOS HABILITADOS POR PERSONAL SERVICIO 1 ===")
df_pp = pd.read_sql_query("""
    SELECT pp.personal_nombre, p.nombre AS puesto
    FROM personal_puestos pp
    JOIN puestos p ON pp.puesto_id = p.id
    WHERE p.servicio_id = 1
""", conn)
print(df_pp)

print("\n=== TURNOS CONFIG SERVICIO 1 ===")
df_t = pd.read_sql_query("""
    SELECT id, nombre, hora_inicio, horas, dias_semana, orden, activo 
    FROM turnos_config 
    WHERE servicio_id = 1
""", conn)
print(df_t)

print("\n=== DEMANDA SERVICIO 1 ===")
df_d = pd.read_sql_query("""
    SELECT puesto_id, tipo_dia, hora_inicio, hora_fin, cantidad_min, cantidad_max 
    FROM demanda_config 
    WHERE puesto_id IN (SELECT id FROM puestos WHERE servicio_id = 1)
""", conn)
print(df_d)

conn.close()
