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

def run_with_replacements(name, replacements):
    # Copy soft_rules.py to scratch/soft_rules_temp.py
    shutil.copy("soft_rules.py", "scratch/soft_rules_temp.py")
    
    with open("scratch/soft_rules_temp.py", "r", encoding="utf-8") as f:
        content = f.read()
        
    # Apply replacements
    # Always disable debug prints to prevent terminal slowdown
    content = content.replace(
        'print(f"DEBUG: Penalizando {nombre} dia {d} turno {t_a_penalizar} peso {peso} es_f={es_f}")',
        'pass # print(...)'
    )
    for target, repl in replacements:
        if target not in content:
            print(f"WARNING: target '{target}' not found in soft_rules.py")
        content = content.replace(target, repl)
        
    with open("scratch/soft_rules_temp.py", "w", encoding="utf-8") as f:
        f.write(content)
        
    # Dynamically import/reload soft_rules_temp
    if "scratch.soft_rules_temp" in sys.modules:
        del sys.modules["scratch.soft_rules_temp"]
    import scratch.soft_rules_temp as soft_rules_temp
    
    # Patch main to use our temp soft rules
    main.aplicar_reglas_blandas = soft_rules_temp.aplicar_reglas_blandas
    
    # Build model
    modelo, turnos, flr_tracker, vars_turno_sem = main.construir_modelo(
        empleados, config_turnos, turnos_dict, demanda_req, adjustments,
        31, [8], offset_dia, 5, reglas_servicio_db, ajustes_reglas,
        historial_semana_previa, data.SERVICIO_ID
    )
    
    # Solve
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 8
    status = solver.Solve(modelo)
    
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print(f"RESULT [{name}]: FACTIBLE")
        return True
    else:
        print(f"RESULT [{name}]: INVIABLE")
        return False

# Group definitions to test by commenting them out
groups = {
    "1_WEEKEND_RATIOM_EQUITY": [
        ("modelo.Add(ratio_finde_mes <= max_ratio_finde_mes)", "pass # modelo.Add(ratio_finde_mes <= max_ratio_finde_mes)"),
        ("modelo.Add(ratio_finde_mes >= min_ratio_finde_mes)", "pass # modelo.Add(ratio_finde_mes >= min_ratio_finde_mes)")
    ],
    "2_WEEKEND_RATIOMCAL_EQUITY": [
        ("modelo.Add(ratio_m <= max_ratio_finde_mes_cal[m])", "pass # modelo.Add(ratio_m <= max_ratio_finde_mes_cal[m])"),
        ("modelo.Add(ratio_m >= min_ratio_finde_mes_cal[m])", "pass # modelo.Add(ratio_m >= min_ratio_finde_mes_cal[m])")
    ],
    "3_WEEKEND_RATIOANUAL_EQUITY": [
        ("modelo.Add(ratio_finde_anual <= max_ratio_finde_anual)", "pass # modelo.Add(ratio_finde_anual <= max_ratio_finde_anual)"),
        ("modelo.Add(ratio_finde_anual >= min_ratio_finde_anual)", "pass # modelo.Add(ratio_finde_anual <= min_ratio_finde_anual)")
    ],
    "4_MONTHLY_HOURS_EQUITY": [
        ("modelo.Add(total_mes <= max_horas_mes)", "pass # modelo.Add(total_mes <= max_horas_mes)"),
        ("modelo.Add(total_mes >= min_horas_mes)", "pass # modelo.Add(total_mes >= min_horas_mes)")
    ],
    "5_MONTHLY_HOURSCAL_EQUITY": [
        ("modelo.Add(total_mes_m <= max_horas_mes_cal[m])", "pass # modelo.Add(total_mes_m <= max_horas_mes_cal[m])"),
        ("modelo.Add(total_mes_m >= min_horas_mes_cal[m])", "pass # modelo.Add(total_mes_m >= min_horas_mes_cal[m])")
    ],
    "6_ANNUAL_HOURS_EQUITY": [
        ("modelo.Add(total_anual_proyectado <= max_anual)", "pass # modelo.Add(total_anual_proyectado <= max_anual)"),
        ("modelo.Add(total_anual_proyectado >= min_anual)", "pass # modelo.Add(total_anual_proyectado >= min_anual)")
    ],
    "7_SEGUIMIENTO_EQUITY": [
        ("modelo.Add(total_seg_proyectado <= max_seg)", "pass # modelo.Add(total_seg_proyectado <= max_seg)"),
        ("modelo.Add(total_seg_proyectado >= min_seg)", "pass # modelo.Add(total_seg_proyectado >= min_seg)")
    ],
    "8_SHIFT_TYPE_EQUITY": [
        ("modelo.Add(sum(semanas_M_persona) <= max_sem_M)", "pass # modelo.Add(sum(semanas_M_persona) <= max_sem_M)"),
        ("modelo.Add(sum(semanas_M_persona) >= min_sem_M)", "pass # modelo.Add(sum(semanas_M_persona) >= min_sem_M)"),
        ("modelo.Add(sum(semanas_T_persona) <= max_sem_T)", "pass # modelo.Add(sum(semanas_T_persona) <= max_sem_T)"),
        ("modelo.Add(sum(semanas_T_persona) >= min_sem_T)", "pass # modelo.Add(sum(semanas_T_persona) >= min_sem_T)"),
        ("modelo.Add(sum(semanas_TN_persona) <= max_sem_TN)", "pass # modelo.Add(sum(semanas_TN_persona) <= max_sem_TN)"),
        ("modelo.Add(sum(semanas_TN_persona) >= min_sem_TN)", "pass # modelo.Add(sum(semanas_TN_persona) >= min_sem_TN)"),
        ("modelo.Add(sum(semanas_N_persona) <= max_sem_N)", "pass # modelo.Add(sum(semanas_N_persona) <= max_sem_N)"),
        ("modelo.Add(sum(semanas_N_persona) >= min_sem_N)", "pass # modelo.Add(sum(semanas_N_persona) >= min_sem_N)")
    ],
    "9_FL_EQUITY": [
        ("modelo.Add(total_fl3 <= max_fl3)", "pass # modelo.Add(total_fl3 <= max_fl3)"),
        ("modelo.Add(total_fl3 >= min_fl3)", "pass # modelo.Add(total_fl3 >= min_fl3)"),
        ("modelo.Add(total_fl4 <= max_fl4)", "pass # modelo.Add(total_fl4 <= max_fl4)"),
        ("modelo.Add(total_fl4 >= min_fl4)", "pass # modelo.Add(total_fl4 >= min_fl4)")
    ],
    "10_DAILY_PERSONAL_GAP_EQUITY": [
        ("modelo.Add(max_dia_t >= total_d)", "pass # modelo.Add(max_dia_t >= total_d)"),
        ("modelo.Add(min_dia_t <= total_d)", "pass # modelo.Add(min_dia_t <= total_d)")
    ],
    "11_COVERAGE_DEFICIT_GAP": [
        ("modelo.Add(deficit_var >= c_max - sum(pool_normales))", "pass # modelo.Add(deficit_var >= c_max - sum(pool_normales))")
    ],
    "12_ALL_BRECHAS_DEFINITIONS": [
        ("modelo.Add(brecha_mensual == max_horas_mes - min_horas_mes)", "pass # modelo.Add(brecha_mensual == max_horas_mes - min_horas_mes)"),
        ("modelo.Add(brecha_anual == max_anual - min_anual)", "pass # modelo.Add(brecha_anual == max_anual - min_anual)"),
        ("modelo.Add(brecha_seg == max_seg - min_seg)", "pass # modelo.Add(brecha_seg == max_seg - min_seg)"),
        ("modelo.Add(brecha_ratio_finde_mes == max_ratio_finde_mes - min_ratio_finde_mes)", "pass # modelo.Add(brecha_ratio_finde_mes == max_ratio_finde_mes - min_ratio_finde_mes)"),
        ("modelo.Add(brecha_ratio_finde_anual == max_ratio_finde_anual - min_ratio_finde_anual)", "pass # modelo.Add(brecha_ratio_finde_anual == max_ratio_finde_anual - min_ratio_finde_anual)")
    ],
    "13_DEBUG_PRINTS": [
        ('print(f"DEBUG: Penalizando {nombre} dia {d} turno {t_a_penalizar} peso {peso} es_f={es_f}")', 'pass # print(...)')
    ]
}

print("=== STARTING INDIVIDUAL GROUP DISABLE TESTS ===")
# First test with nothing disabled
# run_with_replacements("NONE_DISABLED", [])

# Test each group individually
for name, repls in groups.items():
    run_with_replacements(name, repls)

# Test disabling all equity/brecha constraints
all_equity_repls = []
for name, repls in groups.items():
    if name != "13_DEBUG_PRINTS":
        all_equity_repls.extend(repls)
all_equity_repls.extend(groups["13_DEBUG_PRINTS"]) # disable debug print to run fast

print("\n=== TESTING WITH ALL EQUITY/BRECHA CONSTRAINTS DISABLED ===")
run_with_replacements("ALL_EQUITY_DISABLED", all_equity_repls)

# Clean up
if os.path.exists("scratch/soft_rules_temp.py"):
    os.remove("scratch/soft_rules_temp.py")
