import sys
import os
from datetime import date, timedelta, datetime
from ortools.sat.python import cp_model

sys.path.append(os.path.abspath("."))
import data
from database import queries as db_queries
from database.data_loader import obtener_empleados, obtener_turnos
import rule_engine as _re
import scratch.diagnose_unsat as du

db_queries.init_licencias()
fecha_inicio = "2026-06-01"
fecha_fin = "2026-06-30"
servicio_id = 3

fecha_inicio_dt = datetime.strptime(fecha_inicio, "%Y-%m-%d")
fecha_fin_dt = datetime.strptime(fecha_fin, "%Y-%m-%d")
total_dias = (fecha_fin_dt - fecha_inicio_dt).days + 1
num_semanas = (total_dias + 6) // 7

config_turnos, metadata_turnos_raw, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
    servicio_id=servicio_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
)
reglas_servicio_db = db_queries.cargar_reglas_servicio(servicio_id)
ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)
empleados = obtener_empleados(servicio_id, fecha_inicio, total_dias)
turnos_dict = obtener_turnos(servicio_id)
historial_semana_previa = db_queries.cargar_guardias_previas(fecha_inicio, dias_atras=28, servicio_id=servicio_id)
offset_dia = fecha_inicio_dt.weekday()

feriados_indices = []
from data import FERIADOS
for f_str in FERIADOS:
    f_dt = datetime.strptime(f_str, "%Y-%m-%d")
    delta = (f_dt - fecha_inicio_dt).days
    if 0 <= delta < total_dias:
        feriados_indices.append(delta)

planta_doctors = [emp.nombre for emp in empleados if emp.rol != "Residente"]

# We will start with a dictionary containing all Planta doctors to ignore rules for
ignored_doctors = set(planta_doctors)

def solve_with_ignored(ignored):
    ignore_dict = {name: ['MAX_HORAS_MES_CALENDARIO'] for name in ignored}
    args_modelo = (empleados, config_turnos, turnos_dict, demanda_req, ajustes_db, total_dias, feriados_indices, offset_dia, num_semanas, reglas_servicio_db, ajustes_reglas, historial_semana_previa, servicio_id)
    modelo = du.construir_modelo_test(*args_modelo, reglas_a_ignorar_por_persona=ignore_dict)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 5
    status = solver.Solve(modelo)
    return status == cp_model.OPTIMAL or status == cp_model.FEASIBLE

# Verify baseline (all relaxed) is feasible
if not solve_with_ignored(ignored_doctors):
    print("Error: Baseline (all relaxed) is not feasible!")
    sys.exit(1)

print("Starting minimization of ignored doctors...")
# Progresivamente intentamos remover de ignored
for name in list(ignored_doctors):
    test_ignored = ignored_doctors - {name}
    if solve_with_ignored(test_ignored):
        ignored_doctors = test_ignored
        print(f"Removed {name} from ignored set. (Feasible)")
    else:
        print(f"Cannot remove {name} from ignored set. (Required)")

print("\nFinal set of doctors who MUST have their max hours limit relaxed:")
print(ignored_doctors)
