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

all_soft_rules = [
    'PESO_EQUIDAD_FINDES_MENSUAL_CALENDARIO',
    'PESO_EQUIDAD_FINDES_ANUAL',
    'FINDE_LARGO_REGLAMENTARIO_ESTRICTO',
    'BONUS_POR_CARGA_PERFECTA',
    'PESO_INCONSISTENCIA',
    'PENALIZACION_TURNO',
    'PESO_BRECHA_MENSUAL_CALENDARIO',
    'PESO_EQUIDAD_TIPO_TURNO'
]

def run_isolated_test(rule_to_enable):
    db_rules = db_queries.cargar_reglas_servicio(servicio_id)
    reglas_servicio_db = {}
    
    # Required rules
    reglas_servicio_db['LIMITES_SOFT_RULES'] = db_rules['LIMITES_SOFT_RULES']
    reglas_servicio_db['MAX_HORAS_SEMANA'] = db_rules['MAX_HORAS_SEMANA']
    
    # Suspend all soft rules by default
    for r in all_soft_rules:
        reglas_servicio_db[r] = {'suspendida': True}
        
    # Enable the target rule
    if rule_to_enable == 'WEEKENDS':
        reglas_servicio_db['PESO_EQUIDAD_FINDES_MENSUAL_CALENDARIO'] = db_rules.get('PESO_EQUIDAD_FINDES_MENSUAL_CALENDARIO', {'peso': 2000})
        reglas_servicio_db['PESO_EQUIDAD_FINDES_ANUAL'] = db_rules.get('PESO_EQUIDAD_FINDES_ANUAL', {'peso': 500})
    elif rule_to_enable == 'FLR':
        reglas_servicio_db['FINDE_LARGO_REGLAMENTARIO_ESTRICTO'] = db_rules.get('FINDE_LARGO_REGLAMENTARIO_ESTRICTO', {'cantidad': 1})
    elif rule_to_enable == 'CARGA_PERFECTA':
        reglas_servicio_db['BONUS_POR_CARGA_PERFECTA'] = db_rules.get('BONUS_POR_CARGA_PERFECTA', {'bonus': 3000})
    elif rule_to_enable == 'INCONSISTENCIA':
        reglas_servicio_db['PESO_INCONSISTENCIA'] = db_rules.get('PESO_INCONSISTENCIA', {'peso': 500})
    elif rule_to_enable == 'PENALIZACION_TURNO':
        reglas_servicio_db['PENALIZACION_TURNO'] = db_rules.get('PENALIZACION_TURNO', [])
    elif rule_to_enable == 'BRECHA_MENSUAL_CALENDARIO':
        reglas_servicio_db['PESO_BRECHA_MENSUAL_CALENDARIO'] = db_rules.get('PESO_BRECHA_MENSUAL_CALENDARIO', {'peso': 50})
    elif rule_to_enable == 'SHIFT_EQUITY':
        reglas_servicio_db['PESO_EQUIDAD_TIPO_TURNO'] = db_rules.get('PESO_EQUIDAD_TIPO_TURNO', {'peso': 150})
        
    modelo = cp_model.CpModel()
    
    original_aplicar = main.aplicar_reglas_blandas
    
    def patched_aplicar(*args, **kwargs):
        nonlocal reglas_servicio_db
        # We need to make sure rules_servicio is set correctly inside aplicar_reglas_blandas
        # args[4] or regras_servicio is passed
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
    print(f"Only enabled {rule_to_enable or 'NONE':<35} -> {status_map.get(status, 'UNKNOWN')}")

tests = [
    'NONE',
    'WEEKENDS',
    'FLR',
    'CARGA_PERFECTA',
    'INCONSISTENCIA',
    'PENALIZACION_TURNO',
    'BRECHA_MENSUAL_CALENDARIO',
    'SHIFT_EQUITY'
]

print("Running true isolation diagnostics...")
for t in tests:
    run_isolated_test(t)
