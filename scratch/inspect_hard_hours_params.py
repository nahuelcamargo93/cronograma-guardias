import sys
import os

sys.path.append(os.getcwd())

import data
import rule_engine
from database import queries as db_queries
from database.data_loader import obtener_empleados

db_queries.init_licencias()
reglas_servicio = db_queries.cargar_reglas_servicio(data.SERVICIO_ID)
ajustes_personal = db_queries.cargar_ajustes_reglas_personal(data.FECHA_INICIO, data.FECHA_FIN)
empleados = obtener_empleados(data.SERVICIO_ID, data.FECHA_INICIO, 31)

print("Checking MIN and MAX HORAS MES CALENDARIO rules:")
for emp in empleados:
    # July 2026 start is 2026-07-01
    ref_date = "2026-07-01"
    p_min = rule_engine.resolver_parametros_regla('MIN_HORAS_MES_CALENDARIO', emp.nombre, ref_date, reglas_servicio, emp.reglas, ajustes_personal)
    p_max = rule_engine.resolver_parametros_regla('MAX_HORAS_MES_CALENDARIO', emp.nombre, ref_date, reglas_servicio, emp.reglas, ajustes_personal)
    p_cred = rule_engine.resolver_parametros_regla('CREDITO_HORARIO_LICENCIA', emp.nombre, ref_date, reglas_servicio, emp.reglas, ajustes_personal)
    
    print(f"Emp: {emp.nombre:25s} | min_h: {p_min} | max_h: {p_max} | credit: {p_cred} | licencias: {len(emp.dias_licencia)}")
