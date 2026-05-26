import sys
import os

sys.path.append(os.getcwd())

import data
import rule_engine as _re
from database import queries as db_queries
from database.data_loader import obtener_empleados, obtener_turnos

db_queries.init_licencias()
fecha_inicio = data.FECHA_INICIO
fecha_fin = data.FECHA_FIN
servicio_id = 2

reglas_servicio = db_queries.cargar_reglas_servicio(servicio_id)
ajustes_personal = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)
empleados = obtener_empleados(servicio_id, fecha_inicio, 31)

print("LICENSED EMPLOYEES DETAILS:")
for emp in empleados:
    if len(emp.dias_licencia) > 0:
        p_min = _re.resolver_parametros_regla('MIN_HORAS_MES_CALENDARIO', emp.nombre, "2026-07-01", reglas_servicio, emp.reglas, ajustes_personal)
        p_findes = _re.resolver_parametros_regla('MIN_FINDES_MES', emp.nombre, "2026-07-01", reglas_servicio, emp.reglas, ajustes_personal)
        p_exacto_findes = _re.resolver_parametros_regla('EXACTO_FINDES_MES', emp.nombre, "2026-07-01", reglas_servicio, emp.reglas, ajustes_personal)
        p_max = _re.resolver_parametros_regla('MAX_HORAS_MES_CALENDARIO', emp.nombre, "2026-07-01", reglas_servicio, emp.reglas, ajustes_personal)
        p_max_turnos = _re.resolver_parametros_regla('MAX_TURNOS', emp.nombre, "2026-07-01", reglas_servicio, emp.reglas, ajustes_personal)
        print(f"Name: {emp.nombre}")
        print(f"  dias_licencia (indices): {sorted(list(emp.dias_licencia))}")
        print(f"  min_h: {p_min} | max_h: {p_max}")
        print(f"  min_findes: {p_findes} | exacto_findes: {p_exacto_findes}")
        print(f"  max_turnos: {p_max_turnos}")
