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

def run_test(name, disable_carga_perfecta, disable_all_equity):
    shutil.copy("soft_rules.py", "scratch/soft_rules_temp.py")
    with open("scratch/soft_rules_temp.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    content = content.replace(
        'print(f"DEBUG: Penalizando {nombre} dia {d} turno {t_a_penalizar} peso {peso} es_f={es_f}")',
        'pass # print(...)'
    )
    
    if disable_carga_perfecta:
        content = content.replace(
            "if rule_engine.regla_existe(params_bonus) and not rule_engine.regla_suspendida(params_bonus) and turnos_dict:",
            "if False: # bonus carga perfecta"
        )
        
    if disable_all_equity:
        # We will replace the return statement or simplify the objective
        # To make it simple, we can just comment out the whole equity constraints block.
        # Let's see: we can replace from "brecha_mensual = modelo.NewIntVar" to "sum(penalizaciones_ad_hoc)"
        # Or even simpler, let's just make the objective 0.
        # In soft_rules.py, the objective is set on lines 990-1020:
        target_obj = """    modelo.Minimize(
        (brecha_anual * peso_anual) +
        (brecha_mensual * peso_mensual) +
        suma_brechas_mes_cal +
        suma_brechas_finde_mes_cal +
        (brecha_seg * peso_seg) +
        ((max_fl3 - min_fl3) * peso_fl3) + 
        ((max_fl4 - min_fl4) * peso_fl4) +
        (brecha_equidad_turnos * peso_equidad_tipo_turno) +
        sum(penalizaciones_flr) -
        (sum(semanas_seg_totales) * peso_seg_totales) - 
        (sum(puntos_seguimiento) * peso_puntos_seg) - 
        (sum(puntos_combo_finde) * peso_combo_finde) - 
        (sum(puntos_preferencias) * peso_preferencias) +
        (sum(puntos_mix_horario) * peso_mix_horario) +
        (sum(puntos_inconsistencia) * peso_inconsistencia) +
        sum(penalizaciones_ad_hoc) +
        sum(puntos_objetivo_rotacion) +
        sum(puntos_diversidad) - 
        sum(puntos_bonus)
    )"""
        if disable_carga_perfecta:
            replacement_obj = "    modelo.Minimize(0)"
        else:
            replacement_obj = "    modelo.Minimize(-sum(puntos_bonus))"
            
        content = content.replace(target_obj, replacement_obj)
        
    with open("scratch/soft_rules_temp.py", "w", encoding="utf-8") as f:
        f.write(content)
        
    if "scratch.soft_rules_temp" in sys.modules:
        del sys.modules["scratch.soft_rules_temp"]
    import scratch.soft_rules_temp as soft_rules_temp
    
    main.aplicar_reglas_blandas = soft_rules_temp.aplicar_reglas_blandas
    
    modelo, turnos, flr_tracker, vars_turno_sem = main.construir_modelo(
        empleados, config_turnos, turnos_dict, demanda_req, adjustments,
        31, [8], offset_dia, 5, reglas_servicio_db, ajustes_reglas,
        historial_semana_previa, data.SERVICIO_ID
    )
    
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 30
    status = solver.Solve(modelo)
    print(f"Test [{name}]: {solver.StatusName(status)}")
    
    os.remove("scratch/soft_rules_temp.py")

# Test 1: Only Carga Perfecta enabled (no other equity rules/penalties, objective is only to maximize bonus)
run_test("ONLY_CARGA_PERFECTA_ENABLED", disable_carga_perfecta=False, disable_all_equity=True)

# Test 2: No soft rules at all (Minimize 0)
run_test("NO_SOFT_RULES_AT_ALL", disable_carga_perfecta=True, disable_all_equity=True)
