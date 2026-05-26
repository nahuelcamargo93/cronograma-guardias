import sys
import os

sys.path.append(os.getcwd())

import data
from database import queries as db_queries
from database.data_loader import obtener_empleados, obtener_turnos
from debug_imposibilidad import construir_modelo_test, intentar_resolver

db_queries.init_licencias()
fecha_inicio = data.FECHA_INICIO
fecha_fin = data.FECHA_FIN
servicio_id = 2

config_turnos, _, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
    servicio_id=servicio_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
)
turnos_dict = obtener_turnos(servicio_id)
reglas_servicio_db = db_queries.cargar_reglas_servicio(servicio_id)
ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)
empleados = obtener_empleados(servicio_id, fecha_inicio, 31)
historial_semana_previa = db_queries.cargar_guardias_previas(fecha_inicio, dias_atras=28, servicio_id=servicio_id)
offset_dia = 2 # July 1st 2026 is Wednesday (index 2)

# Try turning off MIN_HORAS_MES_CALENDARIO for all employees except one, or for specific subgroups
# Let's see if the issue is with license employees or non-license employees.
print("1. Testing model with MIN_HORAS disabled ONLY for employees WITH licenses:")
empleados_con_lic = [e for e in empleados if len(e.dias_licencia) > 0]
empleados_sin_lic = [e for e in empleados if len(e.dias_licencia) == 0]

print(f"Total employees: {len(empleados)}. Con licencias: {len(empleados_con_lic)}, Sin licencias: {len(empleados_sin_lic)}")

# We can customize the build by subclassing or modifying the rule check.
# Let's inspect hard_rules._aplicar_min_horas_mes_calendario. We can temporarily modify the employees passed to it!
# Wait, we can just modify their rules in memory!
# If we set the rule params to None or suspend it.
# Let's try suspending it for employees with licenses:
for emp in empleados_con_lic:
    # Add a mock temporal adjustment to suspend the rule
    # We can inject it into ajustes_reglas
    ajustes_reglas.setdefault(emp.nombre, []).append({
        'codigo_regla': 'MIN_HORAS_MES_CALENDARIO',
        'fecha_inicio': '2026-07-01',
        'fecha_fin':    '2026-07-31',
        'accion':       'SUSPENDER',
        'params':       None
    })

args_modelo = (empleados, config_turnos, turnos_dict, demanda_req, ajustes_db, 31, [9], offset_dia, 5, reglas_servicio_db, ajustes_reglas, historial_semana_previa, servicio_id)
modelo_con_lic_susp = construir_modelo_test(*args_modelo)
res = intentar_resolver(modelo_con_lic_susp)
print(f"Result with MIN_HORAS suspended for licensed employees: {res}")

# Let's restore and suspend for employees WITHOUT licenses:
ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)
for emp in empleados_sin_lic:
    ajustes_reglas.setdefault(emp.nombre, []).append({
        'codigo_regla': 'MIN_HORAS_MES_CALENDARIO',
        'fecha_inicio': '2026-07-01',
        'fecha_fin':    '2026-07-31',
        'accion':       'SUSPENDER',
        'params':       None
    })

args_modelo = (empleados, config_turnos, turnos_dict, demanda_req, ajustes_db, 31, [9], offset_dia, 5, reglas_servicio_db, ajustes_reglas, historial_semana_previa, servicio_id)
modelo_sin_lic_susp = construir_modelo_test(*args_modelo)
res_sin = intentar_resolver(modelo_sin_lic_susp)
print(f"Result with MIN_HORAS suspended for NON-licensed employees: {res_sin}")
