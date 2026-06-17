import sqlite3
import pandas as pd

conn = sqlite3.connect('cronograma_inteligente.db')

print("=== COLUMNAS DE TURNOS CONFIG ===")
cursor = conn.cursor()
cursor.execute("SELECT * FROM turnos_config LIMIT 1")
print([desc[0] for desc in cursor.description])

print("\n=== TURNOS CONFIG SERVICIO 3 ===")
df_turnos = pd.read_sql_query("""
    SELECT *
    FROM turnos_config
    WHERE servicio_id = 3 AND activo = 1
""", conn)
print(df_turnos)

conn.close()
