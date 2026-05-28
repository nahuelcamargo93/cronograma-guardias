import sqlite3
import datetime
from datetime import timedelta

conn = sqlite3.connect("cronograma_inteligente.db")
cursor = conn.cursor()

# Get demand config for service 3
cursor.execute("""
    SELECT tc.nombre, tc.horas, dc.tipo_dia, dc.cantidad_min
    FROM demanda_config dc
    JOIN turnos_config tc ON dc.puesto_id = tc.puesto_id
    WHERE tc.servicio_id = 3 AND tc.activo = 1 AND dc.puesto_id IN (
        SELECT id FROM puestos WHERE servicio_id = 3 AND nombre != 'Residente'
    )
""")
demand_items = cursor.fetchall()
# Deduplicate because joining on puesto_id without matching tipo_dia or other keys might cause duplicates.
# Let's inspect the actual tables first.
print("Demand config items:")
for row in demand_items:
    print(row)

# Let's query the actual turnos config
cursor.execute("SELECT id, nombre, horas, puesto_id FROM turnos_config WHERE servicio_id = 3")
turnos_config = cursor.fetchall()
print("\nTurnos config:")
for row in turnos_config:
    print(row)

# Let's query puestos
cursor.execute("SELECT id, nombre FROM puestos WHERE servicio_id = 3")
puestos = cursor.fetchall()
print("\nPuestos:")
for row in puestos:
    print(row)

conn.close()
