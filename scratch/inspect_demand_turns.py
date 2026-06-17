import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sqlite3
from database import queries as db_queries

servicio_id = 2
config_turnos, _, _, _ = db_queries.cargar_configuracion_turnos(servicio_id)
print("Config de turnos:")
print("Semana:", list(config_turnos.get("Semana", {}).keys()))
print("Finde_Feriado:", list(config_turnos.get("Finde_Feriado", {}).keys()))
