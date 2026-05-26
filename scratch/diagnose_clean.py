import sys
import os
from ortools.sat.python import cp_model

sys.path.append(os.getcwd())

import data
import main
from database import queries as db_queries
from database.data_loader import obtener_empleados, obtener_turnos

# Initialize and load data
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

def test_solve(disable_rules=None):
    modelo = cp_model.CpModel()
    
    original_aplicar = main.aplicar_reglas_blandas
    
    def patched_aplicar(*args, **kwargs):
        if disable_rules == 'ALL':
            return kwargs.get('vars_turno_sem') or args[12] if len(args) > 12 else None
        return original_aplicar(*args, **kwargs)
        
    main.aplicar_reglas_blandas = patched_aplicar
    
    # Suppress stdout to avoid verbose prints
    old_stdout = sys.stdout
    sys.stdout = open(os.devnull, 'w')
    
    try:
        modelo, turnos, flr_tracker, vars_turno_sem = main.construir_modelo(
            empleados, config_turnos, turnos_dict, demanda_req, adjustments,
            31, [8], offset_dia, 5, reglas_servicio_db, ajustes_reglas,
            historial_semana_previa, data.SERVICIO_ID
        )
        
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 15
        status = solver.Solve(modelo)
    finally:
        sys.stdout.close()
        sys.stdout = old_stdout
        main.aplicar_reglas_blandas = original_aplicar
        
    status_map = {
        cp_model.OPTIMAL: "OPTIMAL",
        cp_model.FEASIBLE: "FEASIBLE",
        cp_model.INFEASIBLE: "INFEASIBLE",
        cp_model.UNKNOWN: "UNKNOWN (Timeout/No Sol)"
    }
    print(f"Result for disable_rules={disable_rules}: {status_map.get(status, 'UNKNOWN')}")

print("Running clean diagnostics...")
test_solve(disable_rules='ALL')
test_solve(disable_rules=None)
