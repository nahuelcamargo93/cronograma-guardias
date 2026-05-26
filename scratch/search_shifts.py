import sqlite3
import pandas as pd

conn = sqlite3.connect("cronograma_inteligente.db")
print("=== UNIQUE SHIFTS FOR ENFERMERIA UTI IN GUARDIAS TABLE ===")
print(pd.read_sql_query("""
    SELECT DISTINCT g.turno, g.horas
    FROM guardias g
    JOIN personal p ON g.nombre = p.nombre
    WHERE p.servicio_id = 2
""", conn))
conn.close()
