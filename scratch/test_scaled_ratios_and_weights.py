import sys
import os
import datetime
from datetime import date, timedelta
from ortools.sat.python import cp_model

sys.path.append(os.getcwd())

# 1. Read soft_rules.py and replace 1000 with 100 for ratios
with open("soft_rules.py", "r", encoding="utf-8") as f:
    code = f.read()

# Replace bounds from 1000 to 100
code = code.replace("modelo.NewIntVar(0, 1000,", "modelo.NewIntVar(0, 100,")
code = code.replace("* 1000", "* 100")

# Write to a temp file
os.makedirs("scratch", exist_ok=True)
with open("scratch/soft_rules_scaled3.py", "w", encoding="utf-8") as f:
    f.write(code)

import data
data.FECHA_INICIO = "2026-07-01"
data.FECHA_FIN = "2026-07-31"
data.SERVICIO_ID = 2

import main
import scratch.soft_rules_scaled3 as soft_rules_scaled3

# Patch aplicar_reglas_blandas
main.aplicar_reglas_blandas = soft_rules_scaled3.aplicar_reglas_blandas

from database import queries as db_queries
from database.data_loader import obtener_empleados, obtener_turnos

# Setup correct dynamic dimensions
fecha_inicio = data.FECHA_INICIO
fecha_fin = data.FECHA_FIN
servicio_id = data.SERVICIO_ID

fecha_inicio_dt = datetime.datetime.strptime(fecha_inicio, "%Y-%m-%d")
fecha_fin_dt    = datetime.datetime.strptime(fecha_fin,    "%Y-%m-%d")
total_dias = (fecha_fin_dt - fecha_inicio_dt).days + 1
DIAS_DEL_BLOQUE = total_dias
num_semanas     = (DIAS_DEL_BLOQUE + 6) // 7

feriados_indices = []
for f_str in data.FERIADOS:
    f_dt = datetime.datetime.strptime(f_str, "%Y-%m-%d")
    delta = (f_dt - fecha_inicio_dt).days
    if 0 <= delta < DIAS_DEL_BLOQUE:
        feriados_indices.append(delta)

config_turnos, metadata_turnos_raw, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
    servicio_id=servicio_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
)
reglas_servicio_db = db_queries.cargar_reglas_servicio(servicio_id)

# Scale up the weekend equity weights by 10 to match the 10x scaled down ratios
if 'PESO_EQUIDAD_FINDES_MENSUAL_CALENDARIO' in reglas_servicio_db:
    w = reglas_servicio_db['PESO_EQUIDAD_FINDES_MENSUAL_CALENDARIO'].get('peso', 500)
    reglas_servicio_db['PESO_EQUIDAD_FINDES_MENSUAL_CALENDARIO']['peso'] = w * 10
if 'PESO_EQUIDAD_FINDES_ANUAL' in reglas_servicio_db:
    w = reglas_servicio_db['PESO_EQUIDAD_FINDES_ANUAL'].get('peso', 500)
    reglas_servicio_db['PESO_EQUIDAD_FINDES_ANUAL']['peso'] = w * 10
if 'PESO_EQUIDAD_FINDES_MENSUAL' in reglas_servicio_db:
    w = reglas_servicio_db['PESO_EQUIDAD_FINDES_MENSUAL'].get('peso', 500)
    reglas_servicio_db['PESO_EQUIDAD_FINDES_MENSUAL']['peso'] = w * 10

ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)
empleados = obtener_empleados(servicio_id, fecha_inicio, DIAS_DEL_BLOQUE)
turnos_dict = obtener_turnos(servicio_id)
historial_semana_previa = db_queries.cargar_guardias_previas(fecha_inicio, dias_atras=28, servicio_id=servicio_id)
offset_dia = fecha_inicio_dt.weekday()

modelo = cp_model.CpModel()

modelo, turnos, flr_tracker, vars_turno_sem = main.construir_modelo(
    empleados, config_turnos, turnos_dict, demanda_req, ajustes_db,
    DIAS_DEL_BLOQUE, feriados_indices, offset_dia, num_semanas, reglas_servicio_db, ajustes_reglas,
    historial_semana_previa, servicio_id
)

solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 180
solver.parameters.log_search_progress = True
status = solver.Solve(modelo)

status_map = {
    cp_model.OPTIMAL: "OPTIMAL",
    cp_model.FEASIBLE: "FEASIBLE",
    cp_model.INFEASIBLE: "INFEASIBLE",
    cp_model.UNKNOWN: "TIMEOUT"
}
print(f"Result with scaled ratios and compensated weights: {status_map.get(status, 'UNKNOWN')}")
