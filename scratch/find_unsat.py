import sys
import os
sys.path.append(os.path.abspath("."))
import sqlite3
from datetime import datetime, date, timedelta
from database.data_loader import obtener_empleados, obtener_turnos
from database import queries as db_queries
from data import FECHA_INICIO, FECHA_FIN, FERIADOS
import main

# Let's load the data
fecha_inicio = "2026-06-01"
fecha_fin = "2026-06-30"

db_schema.inicializar_db() if 'db_schema' in globals() else None
conn = sqlite3.connect("cronograma_inteligente.db")

# Load configuration
config_turnos, metadata_turnos_raw, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
    servicio_id=4, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
)
reglas_servicio_db = db_queries.cargar_reglas_servicio(4)
ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)
empleados = obtener_empleados(4, fecha_inicio, 30)
turnos_dict = obtener_turnos(4)
historial_semana_previa = db_queries.cargar_guardias_previas(fecha_inicio, dias_atras=28, servicio_id=4)
offset_dia = datetime.strptime(fecha_inicio, "%Y-%m-%d").weekday()

print("Rules in service:", reglas_servicio_db.keys())

# We want to test which rule makes it infeasible by building a base model with NO rules, and adding them one by one.
import cp_model_test
