import sys
import os
sys.path.append(os.getcwd())

import data
import soft_rules
import main
from database import queries as db_queries
from database.data_loader import obtener_empleados, obtener_turnos

db_queries.init_licencias()
config_turnos, metadata_turnos_raw, demanda_req, adjustments = db_queries.cargar_configuracion_turnos(
    servicio_id=data.SERVICIO_ID, fecha_inicio=data.FECHA_INICIO, fecha_fin=data.FECHA_FIN
)
reglas_servicio_db = db_queries.cargar_reglas_servicio(data.SERVICIO_ID)
ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(data.FECHA_INICIO, data.FECHA_FIN)
empleados = obtener_empleados(data.SERVICIO_ID, data.FECHA_INICIO, 31)
turnos_dict = obtener_turnos(data.SERVICIO_ID)
historial_semana_previa = db_queries.cargar_guardias_previas(data.FECHA_INICIO, dias_atras=28, servicio_id=data.SERVICIO_ID)
offset_dia = 2 # July 1st 2026 is Wednesday, so weekday is 2

def solve_with(evitar_mezcla, rotacion_mensual):
    print(f"\n--- Probando con EVITAR_MEZCLA_SEMANAL_DURA={evitar_mezcla}, ROTACION_MENSUAL_DURA={rotacion_mensual} ---")
    import hard_rules
    data.EVITAR_MEZCLA_SEMANAL_DURA = evitar_mezcla
    soft_rules.EVITAR_MEZCLA_SEMANAL_DURA = evitar_mezcla
    hard_rules.EVITAR_MEZCLA_SEMANAL_DURA = evitar_mezcla
    
    data.ROTACION_MENSUAL_DURA = rotacion_mensual
    soft_rules.ROTACION_MENSUAL_DURA = rotacion_mensual
    hard_rules.ROTACION_MENSUAL_DURA = rotacion_mensual
    
    modelo, turnos, flr_tracker, vars_turno_sem = main.construir_modelo(
        empleados, config_turnos, turnos_dict, demanda_req, adjustments,
        31, [8], offset_dia, 5, reglas_servicio_db, ajustes_reglas,
        historial_semana_previa, data.SERVICIO_ID
    )
    
    from ortools.sat.python import cp_model
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 15
    status = solver.Solve(modelo)
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print("RESULTADO: FACTIBLE")
    else:
        print("RESULTADO: INVIABLE")

solve_with(True, True)
solve_with(False, True)
solve_with(True, False)
solve_with(False, False)
