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

print(f"Checking Carga Perfecta parameters for SERVICIO_ID = {data.SERVICIO_ID}:")
for emp in empleados:
    nombre = emp.nombre
    params_bonus = rule_engine.resolver_parametros_regla('BONUS_POR_CARGA_PERFECTA', nombre, data.FECHA_INICIO, reglas_servicio, emp.reglas, ajustes_personal)
    if rule_engine.regla_existe(params_bonus):
        print(f"Emp: {nombre:25s} | params: {params_bonus}")
