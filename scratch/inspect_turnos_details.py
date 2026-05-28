import sys
import os
import sqlite3

sys.path.append(os.path.abspath('.'))
from database import queries as db_queries

conn = sqlite3.connect("cronograma_inteligente.db")
cur = conn.cursor()
cur.execute("SELECT id, nombre, hora_inicio, horas, puesto_id, servicio_id FROM turnos_config WHERE servicio_id = 3")
print("turnos_config for Service 3:")
for row in cur.fetchall():
    print(row)
conn.close()
