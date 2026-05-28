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

# Prepare ignore dictionary: ignore MAX_HORAS_MES_CALENDARIO for Planta doctors
ignore_dict = {}
for emp in empleados:
    if emp.rol != "Residente":
        ignore_dict[emp.nombre] = ['MAX_HORAS_MES_CALENDARIO']

args_modelo = (empleados, config_turnos, turnos_dict, demanda_req, ajustes_db, total_dias, feriados_indices, offset_dia, num_semanas, reglas_servicio_db, ajustes_reglas, historial_semana_previa, servicio_id)

print("Building model with MAX_HORAS_MES_CALENDARIO ignored for Planta doctors...")
modelo = du.construir_modelo_test(*args_modelo, reglas_a_ignorar_por_persona=ignore_dict)

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
    print("\nEmployee hours and limit comparison:")
    for emp in empleados:
        # Calculate assigned hours
        assigned_hours = 0
        assigned_shifts = []
        for d in range(total_dias):
            td = "Finde_Feriado" if (d + offset_dia) % 7 >= 5 or d in feriados_indices else "Semana"
            for t in config_turnos.get(td, {}).keys():
                # Reconstruct variable name
                var_name = f'turno_{emp.nombre}_dia{d}_{t}'
                # Search in model variables or similar. Since we used construir_modelo_test, 
                # we don't have direct access to the variables dict here. But wait,
                # we can find it in the solver response by inspecting variables.
                # Actually, cp_model doesn't store variables by name easily in python, but we can reconstruct them
                # or just look at the solution using solver.Value() if we have the variables.
                # Oh, let's write a small helper to get variables from model or rebuild them.
                pass
        
        # To get the assigned hours, let's rebuild the variables just like model did so we can query solver.Value()
        emp_hours = 0
        emp_shifts = []
        for d in range(total_dias):
            dia_semana = (d + offset_dia) % 7
            es_finde_o_feriado = (dia_semana >= 5) or (d in feriados_indices)
            tipo_dia = "Finde_Feriado" if es_finde_o_feriado else "Semana"
            lista_turnos = config_turnos.get(tipo_dia, {}).keys()
            for t in lista_turnos:
                # We need to recreate the variable to query CP-SAT solver
                # Actually,CpModel uses a Proto, we can retrieve the variable by its name from proto!
                pass
        
    # Re-writing variables query in a clean way:
    # Let's inspect the model and fetch variable values by matching their name in the proto!
    vars_by_name = {}
    for i in range(len(modelo.Proto().variables)):
        var_proto = modelo.Proto().variables[i]
        vars_by_name[var_proto.name] = i
        
    for emp in empleados:
        emp_hours = 0
        emp_shifts = []
        for d in range(total_dias):
            dia_semana = (d + offset_dia) % 7
            es_finde_o_feriado = (dia_semana >= 5) or (d in feriados_indices)
            tipo_dia = "Finde_Feriado" if es_finde_o_feriado else "Semana"
            lista_turnos = config_turnos.get(tipo_dia, {}).keys()
            for t in lista_turnos:
                var_name = f'turno_{emp.nombre}_dia{d}_{t}'
                if var_name in vars_by_name:
                    var_idx = vars_by_name[var_name]
                    # Check value in solver
                    val = solver.BooleanValue(var_idx) # CP-SAT python wrapper doesn't have BooleanValue by index easily
                    # Wait, cp_model.CpSolver has Value(var) where var is a IntVar.
                    # If we don't have the IntVar, we can create one referencing the index!
                    var_obj = cp_model.IntVar(modelo.Proto(), var_idx)
                    if solver.Value(var_obj) > 0:
                        h = turnos_dict[t].horas
                        emp_hours += h
                        date_str = (fecha_inicio_dt + timedelta(days=d)).strftime("%a %d")
                        emp_shifts.append(f"{date_str}:{t}({h}h)")
                        
        p_min = _re.resolver_parametros_regla('MIN_HORAS_MES_CALENDARIO', emp.nombre, fecha_inicio, reglas_servicio_db, emp.reglas, ajustes_reglas)
        p_max = _re.resolver_parametros_regla('MAX_HORAS_MES_CALENDARIO', emp.nombre, fecha_inicio, reglas_servicio_db, emp.reglas, ajustes_reglas)
        min_h = p_min.get('min_horas', 0) if (_re.regla_existe(p_min) and not _re.regla_suspendida(p_min)) else 0
        max_h = p_max.get('max_horas', 999) if (_re.regla_existe(p_max) and not _re.regla_suspendida(p_max)) else 999
        
        # Calculate license credit
        dias_lic = [d for d in range(total_dias) if d in emp.dias_licencia]
        p_cred = _re.resolver_parametros_regla('CREDITO_HORARIO_LICENCIA', emp.nombre, fecha_inicio, reglas_servicio_db, emp.reglas, ajustes_reglas)
        if _re.regla_existe(p_cred):
            h_sem = p_cred.get('horas_por_semana', 36)
            horas_lic = int((h_sem / 7.0) * len(dias_lic) + 0.5)
        else:
            horas_lic = int((float(max_h) / total_dias) * len(dias_lic) + 0.5) if max_h != 999 else 0
            
        actual_max = max_h - horas_lic if max_h != 999 else 999
        actual_min = max(0, min_h - horas_lic) if min_h > 0 else 0
        
        exceeded = "!!! EXCEEDED !!!" if emp_hours > actual_max else ""
        print(f"Name: {emp.nombre:35} | Rol: {emp.rol:10} | Assigned: {emp_hours:3d} hs | Range: [{actual_min:3d} - {actual_max:3d}] {exceeded}")
        if exceeded or emp_hours > actual_max:
            print(f"   Shifts: {', '.join(emp_shifts)}")
else:
    print("Could not solve model.")
