import sys
import os
import datetime
from datetime import date, timedelta
from ortools.sat.python import cp_model

sys.path.append(os.getcwd())

import data
data.FECHA_INICIO = "2026-07-01"
data.FECHA_FIN = "2026-07-31"
data.SERVICIO_ID = 2

import main
from database import queries as db_queries
from database.data_loader import obtener_empleados, obtener_turnos

# Setup correct dynamic dimensions
fecha_inicio = data.FECHA_INICIO
fecha_fin = data.FECHA_FIN
servicio_id = data.SERVICIO_ID

fecha_inicio_dt = datetime.datetime.strptime(fecha_inicio, "%Y-%m-%d")
fecha_fin_dt    = datetime.datetime.strptime(fecha_fin,    "%Y-%m-%d")
total_dias = (fecha_fin_dt - fecha_inicio_dt).days + 1
DIAS_DEL_BLOQUE = total_dias
num_semanas     = (DIAS_DEL_BLOQUE + 6) // 7

feriados_indices = []
for f_str in data.FERIADOS:
    f_dt = datetime.datetime.strptime(f_str, "%Y-%m-%d")
    delta = (f_dt - fecha_inicio_dt).days
    if 0 <= delta < DIAS_DEL_BLOQUE:
        feriados_indices.append(delta)

config_turnos, metadata_turnos_raw, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
    servicio_id=servicio_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
)
ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)
empleados = obtener_empleados(servicio_id, fecha_inicio, DIAS_DEL_BLOQUE)
turnos_dict = obtener_turnos(servicio_id)
historial_semana_previa = db_queries.cargar_guardias_previas(fecha_inicio, dias_atras=28, servicio_id=servicio_id)
offset_dia = fecha_inicio_dt.weekday()

def run_test(group_name, disable_weekends=False, disable_flr=False, disable_carga_perfecta=False, disable_shift_equity=False):
    reglas_servicio_db = db_queries.cargar_reglas_servicio(servicio_id)
    
    # We can patch or edit features
    if disable_weekends:
        reglas_servicio_db.pop('PESO_EQUIDAD_FINDES_MENSUAL_CALENDARIO', None)
        reglas_servicio_db.pop('PESO_EQUIDAD_FINDES_ANUAL', None)
    if disable_flr:
        reglas_servicio_db.pop('FINDE_LARGO_REGLAMENTARIO_ESTRICTO', None)
    if disable_carga_perfecta:
        reglas_servicio_db.pop('BONUS_POR_CARGA_PERFECTA', None)
        
    original_aplicar = main.aplicar_reglas_blandas
    
    def patched_aplicar(*args, **kwargs):
        # If we want to disable shift equity, we can modify the rule dict to have weight 0
        nonlocal reglas_servicio_db
        if disable_shift_equity:
            reglas_servicio_db['PESO_EQUIDAD_TIPO_TURNO'] = {'peso': 0}
        else:
            reglas_servicio_db['PESO_EQUIDAD_TIPO_TURNO'] = {'peso': 150}
        return original_aplicar(*args, **kwargs)
        
    main.aplicar_reglas_blandas = patched_aplicar
    
    # Suppress stdout
    old_stdout = sys.stdout
    sys.stdout = open(os.devnull, 'w')
    
    try:
        modelo, turnos, flr_tracker, vars_turno_sem = main.construir_modelo(
            empleados, config_turnos, turnos_dict, demanda_req, ajustes_db,
            DIAS_DEL_BLOQUE, feriados_indices, offset_dia, num_semanas, reglas_servicio_db, ajustes_reglas,
            historial_semana_previa, servicio_id
        )
        
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 10
        status = solver.Solve(modelo)
    finally:
        sys.stdout.close()
        sys.stdout = old_stdout
        
    status_map = {
        cp_model.OPTIMAL: "OPTIMAL",
        cp_model.FEASIBLE: "FEASIBLE",
        cp_model.INFEASIBLE: "INFEASIBLE",
        cp_model.UNKNOWN: "TIMEOUT"
    }
    print(f"{group_name:<50} -> {status_map.get(status, 'UNKNOWN')}")

print("Running group diagnostics...")
run_test("1. Disable Weekends", disable_weekends=True)
run_test("2. Disable FLR", disable_flr=True)
run_test("3. Disable Carga Perfecta", disable_carga_perfecta=True)
run_test("4. Disable Shift Equity", disable_shift_equity=True)
run_test("5. Disable Weekends + FLR", disable_weekends=True, disable_flr=True)
run_test("6. Disable Weekends + Shift Equity", disable_weekends=True, disable_shift_equity=True)
run_test("7. Disable FLR + Shift Equity", disable_flr=True, disable_shift_equity=True)
run_test("8. Disable Weekends + FLR + Shift Equity", disable_weekends=True, disable_flr=True, disable_shift_equity=True)
