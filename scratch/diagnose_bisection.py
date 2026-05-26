import sys
import os
import shutil
from ortools.sat.python import cp_model

sys.path.append(os.getcwd())

import data
import main
from database import queries as db_queries
from database.data_loader import obtener_empleados, obtener_turnos

def run_test_with_lines_disabled(start_line, end_line):
    shutil.copy("soft_rules.py", "scratch/soft_rules_temp.py")
    
    with open("scratch/soft_rules_temp.py", "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    # Replace lines between start_line and end_line (1-indexed) with pass
    for idx in range(start_line - 1, end_line):
        if idx < len(lines):
            # Keep the indentation but replace the rest with pass or comment it out
            indent = len(lines[idx]) - len(lines[idx].lstrip())
            lines[idx] = " " * indent + "pass # disabled in bisection\n"
            
    # Silence debug prints always
    for i in range(len(lines)):
        if 'print(f"DEBUG: Penalizando' in lines[i]:
            indent = len(lines[i]) - len(lines[i].lstrip())
            lines[i] = " " * indent + "pass # print disabled\n"
            
    with open("scratch/soft_rules_temp.py", "w", encoding="utf-8") as f:
        f.writelines(lines)
        
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

# We know that the function starts at line 27 and ends at line 1094.
# Let's divide it into 4 large chunks and test disabling each:
chunks = [
    (27, 250, "Lines 27-250 (Initialization, turnos loops, weekend variables)"),
    (250, 430, "Lines 250-430 (Consistencia anterior, seguimiento loops, combos, mixes)"),
    (430, 600, "Lines 430-600 (Ratio/Nivelacion, mes, anual, preferences)"),
    (600, 800, "Lines 600-800 (FLR, shift type, fl3, fl4, feriados, rotation)"),
    (800, 1000, "Lines 800-1000 (Carga perfecta, brechas global, brecha diaria personal)"),
    (1000, 1094, "Lines 1000-1094 (Deficit, coverage, extra personal, end)")
]

print("=== STARTING LINE-BASED BISECTION DIAGNOSIS ===")
for start, end, desc in chunks:
    res = run_test_with_lines_disabled(start, end)
    print(f"Disable {desc:<70} -> {'FACTIBLE' if res else 'INVIABLE'}")
