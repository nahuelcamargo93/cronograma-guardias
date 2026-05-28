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

def test_each_employee():
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
    ajustes_reglas_base = db_queries.cargar_ajustes_reglas_personal(FECHA_INICIO, FECHA_FIN)
    empleados = obtener_empleados(SERVICIO_ID, FECHA_INICIO, total_dias)
    turnos_dict = obtener_turnos(SERVICIO_ID)
    historial_semana_previa = db_queries.cargar_guardias_previas(FECHA_INICIO, dias_atras=28, servicio_id=SERVICIO_ID)
    offset_dia = fecha_inicio_dt.weekday()

    # Base rules: we disable MIN_HORAS_MES_CALENDARIO globally first
    reglas_servicio_db['MIN_HORAS_MES_CALENDARIO'] = {'min_horas': 192}
    
    # Exceptions we already know:
    known_exceptions = [
        'Godoy Maria',
        'Barloa Matías Damián',
        'Kolarik Jorge Luis',
        'Quintero Anabela Belen',
        'Motta, Mayra Belen'
    ]

    print("Checking which other employees cannot achieve 192 hours:")
    for emp in empleados:
        name = emp.nombre
        if name in known_exceptions:
            continue
            
        # We suspend MIN_HORAS_MES_CALENDARIO for EVERYONE except this specific employee 'name'
        ajustes_reglas = {k: v.copy() for k, v in ajustes_reglas_base.items()}
        for other_emp in empleados:
            other_name = other_emp.nombre
            if other_name != name:
                ajustes_reglas.setdefault(other_name, []).append({
                    'codigo_regla': 'MIN_HORAS_MES_CALENDARIO',
                    'fecha_inicio': FECHA_INICIO,
                    'fecha_fin': FECHA_FIN,
                    'accion': 'SUSPENDER',
                    'params': None
                })
        
        args_modelo = (empleados, config_turnos, turnos_dict, demanda_req, ajustes_db, total_dias, feriados_indices, offset_dia, num_semanas, reglas_servicio_db, ajustes_reglas, historial_semana_previa, SERVICIO_ID)
        modelo_test = construir_modelo_test(*args_modelo)
        
        feasible = intentar_resolver(modelo_test)
        if not feasible:
            print(f"  [FAIL] {name} CANNOT achieve 192 hours!")
        else:
            # Let's print their license days if they have any, just to know
            lic_days = len(emp.dias_licencia)
            lic_msg = f" (has {lic_days} lic days)" if lic_days > 0 else ""
            print(f"  [OK] {name} can achieve 192 hours{lic_msg}")

if __name__ == '__main__':
    test_each_employee()
