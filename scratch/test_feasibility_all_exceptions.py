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
from debug_imposibilidad import construir_modelo_test, intentar_resolver

def test_config():
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

    # General rule
    reglas_servicio_db['MIN_HORAS_MES_CALENDARIO'] = {'min_horas': 192}
    
    # 7 exceptions
    exceptions = [
        'Godoy Maria',
        'Barloa Matías Damián',
        'Kolarik Jorge Luis',
        'Quintero Anabela Belen',
        'Motta, Mayra Belen',
        'Aguilera Graciela',
        'Garcia Rodriguez, Maria Eugenia.'
    ]
    
    for name in exceptions:
        ajustes_reglas.setdefault(name, []).append({
            'codigo_regla': 'MIN_HORAS_MES_CALENDARIO',
            'fecha_inicio': FECHA_INICIO,
            'fecha_fin': FECHA_FIN,
            'accion': 'SUSPENDER',
            'params': None
        })

    args_modelo = (empleados, config_turnos, turnos_dict, demanda_req, ajustes_db, total_dias, feriados_indices, offset_dia, num_semanas, reglas_servicio_db, ajustes_reglas, historial_semana_previa, SERVICIO_ID)
    modelo_base = construir_modelo_test(*args_modelo)
    
    print("Testing feasibility with 7 exceptions...")
    feasible = intentar_resolver(modelo_base)
    if feasible:
        print("[SUCCESS] The model is FEASIBLE with these 7 exceptions!")
    else:
        print("[FAIL] The model is STILL INFEASIBLE.")

if __name__ == '__main__':
    test_config()
