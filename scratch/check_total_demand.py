import sqlite3
import pandas as pd
from datetime import date, timedelta

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

# Get the active service id and dates
cursor.execute("""
    SELECT c.fecha_inicio, c.fecha_fin
    FROM cronogramas c
    WHERE c.id = (SELECT MAX(id) FROM cronogramas)
""")
dates = cursor.fetchone()
fecha_inicio_str, fecha_fin_str = dates
print(f"Active period: {fecha_inicio_str} to {fecha_fin_str}")

# Load all turnos config for Servicio 2
cursor.execute("""
    SELECT tc.nombre, tc.dias_semana
    FROM turnos_config tc
    WHERE tc.servicio_id = 2 AND tc.activo = 1
""")
turnos = cursor.fetchall()
print(f"Service 2 active turnos: {turnos}")

# Let's count how many shifts are generated for each type in this period.
# In main.py:
# We iterate over all days from fecha_inicio to fecha_fin.
# For each day:
# We determine if it is a Weekend/Holiday or Weekday.
# Then we count the demand.
# Wait, let's see how main.py loads the config_turnos and demand.
# Actually, let's query guardias database for the latest cronograma (which is optimal)
# to see how many of each shift were actually assigned in total!
# That represents the total demand/assignments.
query = """
    SELECT g.turno, COUNT(*) as count
    FROM guardias g
    WHERE g.cronograma_id = (SELECT MAX(cronograma_id) FROM guardias)
    GROUP BY g.turno
"""
df_guardias = pd.read_sql_query(query, conn)
print("\nASSIGNED SHIFTS BY TYPE in latest cronograma:")
print(df_guardias.to_string())

conn.close()
