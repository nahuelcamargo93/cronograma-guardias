import sys
import os

sys.path.append(os.getcwd())

import data
from database import queries as db_queries
from database.data_loader import obtener_turnos

turnos_dict = obtener_turnos(data.SERVICIO_ID)
for name, t in turnos_dict.items():
    print(f"Turno: {name:20s} | horas: {t.horas} (type: {type(t.horas)})")
