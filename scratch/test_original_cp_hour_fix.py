import sys
import os
import shutil
from ortools.sat.python import cp_model

sys.path.append(os.getcwd())

import data
import main
from database import queries as db_queries
from database.data_loader import obtener_empleados, obtener_turnos

# Load data once
db_queries.init_licencias()
config_turnos, metadata_turnos_raw, demanda_req, adjustments = db_queries.cargar_configuracion_turnos(
    servicio_id=data.SERVICIO_ID, fecha_inicio=data.FECHA_INICIO, fecha_fin=data.FECHA_FIN
)
reglas_servicio_db = db_queries.cargar_reglas_servicio(data.SERVICIO_ID)
ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(data.FECHA_INICIO, data.FECHA_FIN)
empleados = obtener_empleados(data.SERVICIO_ID, data.FECHA_INICIO, 31)
turnos_dict = obtener_turnos(data.SERVICIO_ID)
historial_semana_previa = db_queries.cargar_guardias_previas(data.FECHA_INICIO, dias_atras=28, servicio_id=data.SERVICIO_ID)
offset_dia = 2 # July 1st 2026 is Wednesday

shutil.copy("soft_rules.py", "scratch/soft_rules_temp.py")

with open("scratch/soft_rules_temp.py", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace(
    'print(f"DEBUG: Penalizando {nombre} dia {d} turno {t_a_penalizar} peso {peso} es_f={es_f}")',
    'pass # print(...)'
)

# Fix 1: Correct the hour calculation for equity to use actual shift hours
target_h_calc = 'h = 12 if (es_finde or t.startswith("Noche")) else 6'
correct_h_calc = 'h = turnos_dict[t].horas if t in turnos_dict else 6'
content = content.replace(target_h_calc, correct_h_calc)

# We do NOT simplify Carga Perfecta here, we keep the original reified constraints

with open("scratch/soft_rules_temp.py", "w", encoding="utf-8") as f:
    f.write(content)

if "scratch.soft_rules_temp" in sys.modules:
    del sys.modules["scratch.soft_rules_temp"]
import scratch.soft_rules_temp as soft_rules_temp

main.aplicar_reglas_blandas = soft_rules_temp.aplicar_reglas_blandas

# Build model
print("Building model with original Carga Perfecta but corrected hours...")
modelo, turnos, flr_tracker, vars_turno_sem = main.construir_modelo(
    empleados, config_turnos, turnos_dict, demanda_req, adjustments,
    31, [8], offset_dia, 5, reglas_servicio_db, ajustes_reglas,
    historial_semana_previa, data.SERVICIO_ID
)

# Solve
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 180 # 3 minutes
solver.parameters.log_search_progress = True
print("Solving model...")
status = solver.Solve(modelo)
print("Status:", solver.StatusName(status))
print("ResponseProto Status:", status)

if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    print("SUCCESS: FACTIBLE / OPTIMAL")
    print(f"Objective Value: {solver.ObjectiveValue()}")
else:
    print("FAIL: INVIABLE / UNKNOWN")

os.remove("scratch/soft_rules_temp.py")
