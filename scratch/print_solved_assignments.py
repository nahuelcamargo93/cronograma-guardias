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

ignore_dict = {
    "Quintero Anabela Belen": ['MAX_HORAS_MES_CALENDARIO']
}

args_modelo = (empleados, config_turnos, turnos_dict, demanda_req, ajustes_db, total_dias, feriados_indices, offset_dia, num_semanas, reglas_servicio_db, ajustes_reglas, historial_semana_previa, servicio_id)

modelo = du.construir_modelo_test(*args_modelo, reglas_a_ignorar_por_persona=ignore_dict)
solver = cp_model.CpSolver()
status = solver.Solve(modelo)

if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    vars_by_name = {modelo.Proto().variables[i].name: i for i in range(len(modelo.Proto().variables))}
    
    # We will group assignments by day and shift
    print("=== DAILY ASSIGNMENTS ===")
    for d in range(total_dias):
        date_str = (fecha_inicio_dt + timedelta(days=d)).strftime("%Y-%m-%d (%a)")
        day_shifts = []
        
        dia_semana = (d + offset_dia) % 7
        es_finde = (dia_semana >= 5) or (d in feriados_indices)
        tipo_dia = "Finde_Feriado" if es_finde else "Semana"
        
        for t in config_turnos.get(tipo_dia, {}).keys():
            for emp in empleados:
                var_name = f'turno_{emp.nombre}_dia{d}_{t}'
                if var_name in vars_by_name:
                    var_idx = vars_by_name[var_name]
                    var_obj = cp_model.IntVar(modelo.Proto(), var_idx)
                    if solver.Value(var_obj) > 0:
                        day_shifts.append(f"{t}: {emp.nombre}")
                        
        print(f"Day {d+1:2d} | {date_str} : {', '.join(day_shifts)}")
else:
    print("Failed to solve.")
