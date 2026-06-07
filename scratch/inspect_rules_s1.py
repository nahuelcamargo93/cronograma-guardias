import sqlite3
import pandas as pd

conn = sqlite3.connect('cronograma_inteligente.db')

print("--- REGLAS SERVICIO 1 ---")
df_rules = pd.read_sql_query("""
    SELECT codigo_regla, parametros_json, activo
    FROM servicios_reglas 
    WHERE servicio_id = 1
""", conn)
print(df_rules)

print("\n--- REGLAS PERSONAL SERVICIO 1 ---")
df_p_rules = pd.read_sql_query("""
    SELECT pr.personal_nombre, pr.codigo_regla, pr.parametros_json, pr.activo
    FROM personal_reglas pr
    JOIN personal p ON pr.personal_nombre = p.nombre
    WHERE p.servicio_id = 1
""", conn)
print(df_p_rules)

print("\n--- PUESTOS Y TURNOS CONFIG DEL SERVICIO 1 ---")
df_puestos = pd.read_sql_query("""
    SELECT id, nombre, servicio_id FROM puestos WHERE servicio_id = 1
""", conn)
print(df_puestos)

df_turnos = pd.read_sql_query("""
    SELECT id, nombre, puesto_id, horas, dias_semana, orden, activo
    FROM turnos_config 
    WHERE servicio_id = 1
""", conn)
print(df_turnos)

conn.close()
