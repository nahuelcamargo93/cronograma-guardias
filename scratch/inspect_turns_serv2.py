import sqlite3
import pandas as pd

conn = sqlite3.connect('cronograma_inteligente.db')

print("=== CONFIGURACION DE TURNOS SERVICIO 2 ===")
df_t = pd.read_sql_query("""
    SELECT id, nombre, sigla, activo, puesto_id 
    FROM turnos_config 
    WHERE servicio_id = 2
""", conn)
print(df_t)

conn.close()
