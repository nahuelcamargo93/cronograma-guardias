import sys
import os
import shutil
from ortools.sat.python import cp_model

sys.path.append(os.getcwd())

import data
import main
from database import queries as db_queries
from database.data_loader import obtener_empleados, obtener_turnos

def run_test(disable_feriados=False, disable_flr=False, disable_carga_perfecta=False, disable_all_equity=False):
    shutil.copy("soft_rules.py", "scratch/soft_rules_temp.py")
    
    with open("scratch/soft_rules_temp.py", "r", encoding="utf-8") as f:
        content = f.read()
        
    content = content.replace(
        'print(f"DEBUG: Penalizando {nombre} dia {d} turno {t_a_penalizar} peso {peso} es_f={es_f}")',
        'pass # print(...)'
    )
    
    if disable_feriados:
        content = content.replace(
            "params_feriados = rule_engine.resolver_parametros_regla('PESO_EQUIDAD_FERIADOS', nombre, FECHA_INICIO, reglas_servicio, emp.reglas, ajustes_personal)",
            "params_feriados = ... # disabled"
        )
    if disable_flr:
        content = content.replace(
            "if active_flr_rule:",
            "if False: # disabled"
        )
    if disable_carga_perfecta:
        content = content.replace(
            "if rule_engine.regla_existe(params_bonus) and not rule_engine.regla_suspendida(params_bonus) and turnos_dict:",
            "if False: # disabled"
        )
    if disable_all_equity:
        equity_replacements = [
            ("modelo.Add(ratio_finde_mes <= max_ratio_finde_mes)", "pass"),
            ("modelo.Add(ratio_finde_mes >= min_ratio_finde_mes)", "pass"),
            ("modelo.Add(ratio_m <= max_ratio_finde_mes_cal[m])", "pass"),
            ("modelo.Add(ratio_m >= min_ratio_finde_mes_cal[m])", "pass"),
            ("modelo.Add(ratio_finde_anual <= max_ratio_finde_anual)", "pass"),
            ("modelo.Add(ratio_finde_anual >= min_ratio_finde_anual)", "pass"),
            ("modelo.Add(total_mes <= max_horas_mes)", "pass"),
            ("modelo.Add(total_mes >= min_horas_mes)", "pass"),
            ("modelo.Add(total_mes_m <= max_horas_mes_cal[m])", "pass"),
            ("modelo.Add(total_mes_m >= min_horas_mes_cal[m])", "pass"),
            ("modelo.Add(total_anual_proyectado <= max_anual)", "pass"),
            ("modelo.Add(total_anual_proyectado >= min_anual)", "pass"),
            ("modelo.Add(total_seg_proyectado <= max_seg)", "pass"),
            ("modelo.Add(total_seg_proyectado >= min_seg)", "pass"),
            ("modelo.Add(sum(semanas_M_persona) <= max_sem_M)", "pass"),
            ("modelo.Add(sum(semanas_M_persona) >= min_sem_M)", "pass"),
            ("modelo.Add(sum(semanas_T_persona) <= max_sem_T)", "pass"),
            ("modelo.Add(sum(semanas_T_persona) >= min_sem_T)", "pass"),
            ("modelo.Add(sum(semanas_TN_persona) <= max_sem_TN)", "pass"),
            ("modelo.Add(sum(semanas_TN_persona) >= min_sem_TN)", "pass"),
            ("modelo.Add(sum(semanas_N_persona) <= max_sem_N)", "pass"),
            ("modelo.Add(sum(semanas_N_persona) >= min_sem_N)", "pass"),
            ("modelo.Add(total_fl3 <= max_fl3)", "pass"),
            ("modelo.Add(total_fl3 >= min_fl3)", "pass"),
            ("modelo.Add(total_fl4 <= max_fl4)", "pass"),
            ("modelo.Add(total_fl4 >= min_fl4)", "pass"),
            ("modelo.Add(max_dia_t >= total_d)", "pass"),
            ("modelo.Add(min_dia_t <= total_d)", "pass"),
            ("modelo.Add(deficit_var >= c_max - sum(pool_normales))", "pass"),
            ("modelo.Add(brecha_mensual == max_horas_mes - min_horas_mes)", "pass"),
            ("modelo.Add(brecha_anual == max_anual - min_anual)", "pass"),
            ("modelo.Add(brecha_seg == max_seg - min_seg)", "pass"),
            ("modelo.Add(brecha_ratio_finde_mes == max_ratio_finde_mes - min_ratio_finde_mes)", "pass"),
            ("modelo.Add(brecha_ratio_finde_anual == max_ratio_finde_anual - min_ratio_finde_anual)", "pass"),
            ("modelo.Add(b_m == max_horas_mes_cal[m] - min_horas_mes_cal[m])", "pass"),
            ("modelo.Add(bf_m == max_ratio_finde_mes_cal[m] - min_ratio_finde_mes_cal[m])", "pass"),
        ]
        for target, repl in equity_replacements:
            content = content.replace(target, repl)

    with open("scratch/soft_rules_temp.py", "w", encoding="utf-8") as f:
        f.write(content)
        
    if "scratch.soft_rules_temp" in sys.modules:
        del sys.modules["scratch.soft_rules_temp"]
    import scratch.soft_rules_temp as soft_rules_temp
    
    main.aplicar_reglas_blandas = soft_rules_temp.aplicar_reglas_blandas
    
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
    
    modelo, turnos, flr_tracker, vars_turno_sem = main.construir_modelo(
        empleados, config_turnos, turnos_dict, demanda_req, adjustments,
        31, [8], offset_dia, 5, reglas_servicio_db, ajustes_reglas,
        historial_semana_previa, data.SERVICIO_ID
    )
    
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 8
    status = solver.Solve(modelo)
    
    os.remove("scratch/soft_rules_temp.py")
    return status == cp_model.OPTIMAL or status == cp_model.FEASIBLE

def run_test_empty():
    shutil.copy("soft_rules.py", "scratch/soft_rules_temp.py")
    with open("scratch/soft_rules_temp.py", "w", encoding="utf-8") as f:
        f.write("def aplicar_reglas_blandas(modelo, turnos, empleados, demanda_turnos, turnos_dict, dias_del_bloque, feriados, offset_dia, num_semanas, servicio_id=1, flr_tracker=None, historial_semana_previa=None, demanda_req=None, ajustes_demanda=None, vars_turno_sem=None):\n    return vars_turno_sem\n")
        
    if "scratch.soft_rules_temp" in sys.modules:
        del sys.modules["scratch.soft_rules_temp"]
    import scratch.soft_rules_temp as soft_rules_temp
    main.aplicar_reglas_blandas = soft_rules_temp.aplicar_reglas_blandas
    
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
    
    modelo, turnos, flr_tracker, vars_turno_sem = main.construir_modelo(
        empleados, config_turnos, turnos_dict, demanda_req, adjustments,
        31, [8], offset_dia, 5, reglas_servicio_db, ajustes_reglas,
        historial_semana_previa, data.SERVICIO_ID
    )
    
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 8
    status = solver.Solve(modelo)
    
    os.remove("scratch/soft_rules_temp.py")
    return status == cp_model.OPTIMAL or status == cp_model.FEASIBLE

print("Testing different rule disable scenarios:")
print("1. Disable Feriados Equity ->", "FACTIBLE" if run_test(disable_feriados=True) else "INVIABLE")
print("2. Disable FLR ->", "FACTIBLE" if run_test(disable_flr=True) else "INVIABLE")
print("3. Disable Carga Perfecta ->", "FACTIBLE" if run_test(disable_carga_perfecta=True) else "INVIABLE")
print("4. Disable Feriados + All Equity ->", "FACTIBLE" if run_test(disable_feriados=True, disable_all_equity=True) else "INVIABLE")
print("5. Disable FLR + All Equity ->", "FACTIBLE" if run_test(disable_flr=True, disable_all_equity=True) else "INVIABLE")
print("6. Disable FLR + Feriados + All Equity ->", "FACTIBLE" if run_test(disable_flr=True, disable_feriados=True, disable_all_equity=True) else "INVIABLE")
print("7. Completely Empty Soft Rules ->", "FACTIBLE" if run_test_empty() else "INVIABLE")

