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

# Suspend EXACTO_FINDES_MES and MIN_FINDES_MES globally:
reglas_servicio_db['EXACTO_FINDES_MES'] = {"exacto_findes": 2, "dinamico_licencias": True, "suspendida": True}
reglas_servicio_db['MIN_FINDES_MES'] = {"min_findes": 2, "dinamico_licencias": True, "suspendida": True}

args_modelo = (empleados, config_turnos, turnos_dict, demanda_req, ajustes_db, total_dias, feriados_indices, offset_dia, num_semanas, reglas_servicio_db, ajustes_reglas, historial_semana_previa, servicio_id)

print("Building model with EXACTO_FINDES_MES suspended globally...")
modelo = du.construir_modelo_test(*args_modelo)

print("Solving...")
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 20
status = solver.Solve(modelo)

status_names = {
    cp_model.OPTIMAL: "OPTIMAL",
    cp_model.FEASIBLE: "FEASIBLE",
    cp_model.INFEASIBLE: "INFEASIBLE",
    cp_model.MODEL_INVALID: "MODEL_INVALID",
    cp_model.UNKNOWN: "UNKNOWN"
}

print(f"Status: {status_names.get(status, 'UNKNOWN')}")

if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    vars_by_name = {modelo.Proto().variables[i].name: i for i in range(len(modelo.Proto().variables))}
    for emp in empleados:
        emp_hours = 0
        emp_shifts = []
        for d in range(total_dias):
            dia_semana = (d + offset_dia) % 7
            es_finde = (dia_semana >= 5) or (d in feriados_indices)
            tipo_dia = "Finde_Feriado" if es_finde else "Semana"
            for t in config_turnos.get(tipo_dia, {}).keys():
                var_name = f'turno_{emp.nombre}_dia{d}_{t}'
                if var_name in vars_by_name:
                    var_idx = vars_by_name[var_name]
                    var_obj = cp_model.IntVar(modelo.Proto(), var_idx)
                    if solver.Value(var_obj) > 0:
                        h = turnos_dict[t].horas
                        emp_hours += h
                        date_str = (fecha_inicio_dt + timedelta(days=d)).strftime("%a %d")
                        emp_shifts.append(f"{date_str}:{t}({h}h)")
        p_max = _re.resolver_parametros_regla('MAX_HORAS_MES_CALENDARIO', emp.nombre, fecha_inicio, reglas_servicio_db, emp.reglas, ajustes_reglas)
        max_h = p_max.get('max_horas', 999) if (_re.regla_existe(p_max) and not _re.regla_suspendida(p_max)) else 999
        dias_lic = [d for d in range(total_dias) if d in emp.dias_licencia]
        p_cred = _re.resolver_parametros_regla('CREDITO_HORARIO_LICENCIA', emp.nombre, fecha_inicio, reglas_servicio_db, emp.reglas, ajustes_reglas)
        if _re.regla_existe(p_cred):
            h_sem = p_cred.get('horas_por_semana', 36)
            horas_lic = int((h_sem / 7.0) * len(dias_lic) + 0.5)
        else:
            horas_lic = int((float(max_h) / total_dias) * len(dias_lic) + 0.5) if max_h != 999 else 0
        actual_max = max_h - horas_lic if max_h != 999 else 999
        p_min = _re.resolver_parametros_regla('MIN_HORAS_MES_CALENDARIO', emp.nombre, fecha_inicio, reglas_servicio_db, emp.reglas, ajustes_reglas)
        min_h = p_min.get('min_horas', 0) if (_re.regla_existe(p_min) and not _re.regla_suspendida(p_min)) else 0
        actual_min = max(0, min_h - horas_lic)
        
        exceeded = "!!! EXCEEDED !!!" if emp_hours > actual_max else ""
        print(f"Name: {emp.nombre:35} | Assigned: {emp_hours:3d} hs | Range: [{actual_min:3d} - {actual_max:3d}] {exceeded}")
        if exceeded:
            print(f"   Shifts: {', '.join(emp_shifts)}")
else:
    print("Could not solve model.")
