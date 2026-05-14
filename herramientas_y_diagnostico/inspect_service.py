import sqlite3
import pandas as pd

conn = sqlite3.connect('cronograma_inteligente.db')

print("--- SERVICIOS ---")
print(pd.read_sql_query("SELECT * FROM servicios", conn))

print("\n--- PERSONAL (SERVICIO 2) ---")
print(pd.read_sql_query("SELECT nombre, rol, servicio_id FROM personal WHERE servicio_id = 2", conn))

print("\n--- TURNOS CONFIG (SERVICIO 2) ---")
print(pd.read_sql_query("SELECT * FROM turnos_config WHERE servicio_id = 2", conn))

print("\n--- REGLAS SERVICIO (SERVICIO 2) ---")
print(pd.read_sql_query("""
    SELECT rc.codigo_regla, sr.parametros_json 
    FROM servicios_reglas sr 
    JOIN reglas_catalogo rc ON sr.regla_id = rc.id 
    WHERE sr.servicio_id = 2
""", conn))

conn.close()
