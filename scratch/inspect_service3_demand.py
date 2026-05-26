import sqlite3
import pandas as pd

conn = sqlite3.connect("cronograma_inteligente.db")
print("=== PUESTOS FOR SERVICE 3 ===")
print(pd.read_sql_query("SELECT id, nombre FROM puestos WHERE servicio_id = 3", conn))

print("\n=== DEMANDA CONFIG FOR SERVICE 3 ===")
print(pd.read_sql_query("""
    SELECT dc.*, p.nombre as puesto_nombre
    FROM demanda_config dc
    JOIN puestos p ON dc.puesto_id = p.id
    WHERE p.servicio_id = 3
""", conn))

print("\n=== TURNOS CONFIG FOR SERVICE 3 ===")
print(pd.read_sql_query("SELECT * FROM turnos_config WHERE servicio_id = 3", conn))
conn.close()
