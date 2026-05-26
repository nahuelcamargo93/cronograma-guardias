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
    # Create a fresh model
    modelo = cp_model.CpModel()
    
    # We will build the model ourselves or modify the build process.
    # Let's inspect main.construir_modelo:
    # We want to run construir_modelo, but intercept or patch soft_rules.
    import main
    original_aplicar = main.aplicar_reglas_blandas
    
    def patched_aplicar(*args, **kwargs):
        if disable_rules == 'ALL':
            print("Skipping all soft rules...")
            return kwargs.get('vars_turno_sem') or args[12] if len(args) > 12 else None
        
        # If we want to selectively run parts:
        # Let's inspect what happens. We can just run the original for now to see.
        return original_aplicar(*args, **kwargs)
        
    main.aplicar_reglas_blandas = patched_aplicar
    
    try:
        modelo, turnos, flr_tracker, vars_turno_sem = main.construir_modelo(
            empleados, config_turnos, turnos_dict, demanda_req, adjustments,
            31, [8], offset_dia, 5, reglas_servicio_db, ajustes_reglas,
            historial_semana_previa, data.SERVICIO_ID
        )
        
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 10
        print(f"Solving (disable_rules={disable_rules})...")
        status = solver.Solve(modelo)
        
        if status == cp_model.OPTIMAL:
            print("Status: OPTIMAL")
        elif status == cp_model.FEASIBLE:
            print("Status: FEASIBLE")
        elif status == cp_model.INFEASIBLE:
            print("Status: INFEASIBLE")
        else:
            print("Status: UNKNOWN (Timeout or error)")
    finally:
        main.aplicar_reglas_blandas = original_aplicar

print("--- TEST 1: NO SOFT RULES ---")
test_solve(disable_rules='ALL')

print("\n--- TEST 2: WITH ALL ORIGINAL SOFT RULES ---")
test_solve(disable_rules=None)
