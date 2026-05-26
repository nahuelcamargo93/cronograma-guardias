import sqlite3
import pandas as pd

conn = sqlite3.connect("cronograma_inteligente.db")
print("=== TURNOS CONFIG FOR ENFERMERIA UTI (servicio_id = 2) ===")
print(pd.read_sql_query("SELECT * FROM turnos_config WHERE servicio_id = 2", conn))

print("\n=== DEMANDA CONFIG FOR ENFERMERIA UTI ===")
print(pd.read_sql_query("""
    SELECT dc.*, p.nombre as puesto_nombre
    FROM demanda_config dc
    JOIN puestos p ON dc.puesto_id = p.id
    WHERE p.servicio_id = 2
""", conn))

print("\n=== PUESTOS FOR ENFERMERIA UTI ===")
print(pd.read_sql_query("SELECT * FROM puestos WHERE servicio_id = 2", conn))

conn.close()
