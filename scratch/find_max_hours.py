import sys
sys.path.insert(0, 'c:/Users/asus/Desktop/Ryoko/cronograma_inteligente')

import pandas as pd
import datetime
from datetime import date, timedelta
from ortools.sat.python import cp_model
from data import FECHA_INICIO, FECHA_FIN, FERIADOS, SERVICIO_ID
from database import queries as db_queries
from database import schema as db_schema
from database.data_loader import obtener_empleados, obtener_turnos
import rule_engine as _re
from debug_imposibilidad import construir_modelo_test

def find_max_hours():
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
    empleados = obtener_empleados(SERVICIO_ID, FECHA_INICIO, total_dias)
    turnos_dict = obtener_turnos(SERVICIO_ID)
    historial_semana_previa = db_queries.cargar_guardias_previas(FECHA_INICIO, dias_atras=28, servicio_id=SERVICIO_ID)
    offset_dia = fecha_inicio_dt.weekday()

    # Disable MIN_HORAS_MES_CALENDARIO so we don't cause infeasibility
    if 'MIN_HORAS_MES_CALENDARIO' in reglas_servicio_db:
        del reglas_servicio_db['MIN_HORAS_MES_CALENDARIO']

    from main import construir_modelo
    
    # We want to maximize the hours worked by Aguilera Graciela and Garcia Rodriguez
    names = ['Aguilera Graciela', 'Garcia Rodriguez, Maria Eugenia.']
    for name in names:
        # Build model using main's builder:
        # (Notice that main.py applies MIN_HORAS_MES_CALENDARIO. So we should suspend it first).
        # To suspend it for everyone, we can just suspend it in reglas_servicio_db or ajustes_reglas.
        
        reglas_servicio_db['MIN_HORAS_MES_CALENDARIO'] = {'min_horas': 192}
        
        test_ajustes = {k: v.copy() for k, v in ajustes_reglas.items()}
        for emp in empleados:
            test_ajustes.setdefault(emp.nombre, []).append({
                'codigo_regla': 'MIN_HORAS_MES_CALENDARIO',
                'fecha_inicio': FECHA_INICIO,
                'fecha_fin': FECHA_FIN,
                'accion': 'SUSPENDER',
                'params': None
            })
            
        modelo, turnos, flr_tracker, vars_turno_sem = construir_modelo(
            empleados, config_turnos, turnos_dict, demanda_req, ajustes_db,
            total_dias, feriados_indices, offset_dia, num_semanas,
            reglas_servicio_db, test_ajustes, historial_semana_previa, SERVICIO_ID
        )
        
        # Sum of (variable * hours) for this employee
        emp_vars = []
        for (n, d, t), var in turnos.items():
            if n == name:
                h_turno = turnos_dict[t].horas
                emp_vars.append(var * h_turno)
        
        # Maximize this employee's hours
        modelo.Maximize(sum(emp_vars))
        
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 10
        status = solver.Solve(modelo)
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            print(f"Max hours for {name}: {solver.ObjectiveValue()}")
        else:
            print(f"Could not solve for {name} status: {status}")

find_max_hours()
