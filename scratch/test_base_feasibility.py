import datetime
from datetime import date, timedelta
import time
from ortools.sat.python import cp_model
from database import queries as db_queries
from database import schema as db_schema
from database.data_loader import obtener_empleados, obtener_turnos
from data import FECHA_INICIO, FECHA_FIN, FERIADOS, SERVICIO_ID
import rule_engine as _re
from debug_imposibilidad import construir_modelo_test

def test_base_feasibility():
    db_schema.inicializar_db()
    db_queries.init_licencias()
    
    fecha_inicio_dt = datetime.datetime.strptime(FECHA_INICIO, "%Y-%m-%d")
    fecha_fin_dt    = datetime.datetime.strptime(FECHA_FIN,    "%Y-%m-%d")
    total_dias = (fecha_fin_dt - fecha_inicio_dt).days + 1
    num_semanas = (total_dias + 6) // 7

    feriados_indices = []
    for f_str in FERIADOS:
        f_dt = datetime.datetime.strptime(f_str, "%Y-%m-%d")
        delta = (f_dt - fecha_inicio_dt).days
        if 0 <= delta < total_dias:
            feriados_indices.append(delta)

    config_turnos, metadata_turnos_raw, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
        servicio_id=SERVICIO_ID, fecha_inicio=FECHA_INICIO, fecha_fin=FECHA_FIN
    )
    reglas_servicio_db = db_queries.cargar_reglas_servicio(SERVICIO_ID)
    ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(FECHA_INICIO, FECHA_FIN)
    
    ajustes_servicio = db_queries.cargar_ajustes_reglas_servicio(FECHA_INICIO, FECHA_FIN, SERVICIO_ID)
    ajustes_reglas['__servicio__'] = ajustes_servicio
    
    empleados = obtener_empleados(SERVICIO_ID, FECHA_INICIO, total_dias)
    turnos_dict = obtener_turnos(SERVICIO_ID)
    historial_semana_previa = db_queries.cargar_guardias_previas(FECHA_INICIO, dias_atras=28, servicio_id=SERVICIO_ID)
    offset_dia = fecha_inicio_dt.weekday()

    args_modelo = (empleados, config_turnos, turnos_dict, demanda_req, ajustes_db, total_dias, feriados_indices, offset_dia, num_semanas, reglas_servicio_db, ajustes_reglas, historial_semana_previa, SERVICIO_ID)

    # 1. Test base without REGLAS_BLANDAS (with 15s timeout and 8 workers)
    print("Testing base model WITHOUT soft rules...")
    modelo_no_soft = construir_modelo_test(*args_modelo, reglas_a_ignorar=['REGLAS_BLANDAS'])
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 15.0
    solver.parameters.num_search_workers = 8
    
    t0 = time.time()
    status = solver.Solve(modelo_no_soft)
    t1 = time.time()
    
    viable = (status == cp_model.OPTIMAL or status == cp_model.FEASIBLE)
    print(f"Result: Viable={viable} | Status={status} | Time={t1-t0:.3f}s")
    
    # 2. Test base WITH REGLAS_BLANDAS (with 30s timeout and 8 workers)
    print("Testing base model WITH soft rules...")
    modelo_with_soft = construir_modelo_test(*args_modelo)
    solver2 = cp_model.CpSolver()
    solver2.parameters.max_time_in_seconds = 30.0
    solver2.parameters.num_search_workers = 8
    
    t0 = time.time()
    status2 = solver2.Solve(modelo_with_soft)
    t1 = time.time()
    
    viable2 = (status2 == cp_model.OPTIMAL or status2 == cp_model.FEASIBLE)
    print(f"Result: Viable={viable2} | Status={status2} | Time={t1-t0:.3f}s")

if __name__ == '__main__':
    test_base_feasibility()
