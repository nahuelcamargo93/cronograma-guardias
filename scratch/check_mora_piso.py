import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import queries as db_queries
from database.data_loader import obtener_empleados
from datetime import date
import rule_engine as _re

db_queries.init_licencias(3)
empleados = obtener_empleados(3, "2026-07-01", 31)
reglas_servicio = db_queries.cargar_reglas_servicio(3)
ajustes_reglas = db_queries.cargar_ajustes_reglas_personal("2026-07-01", "2026-07-31")

for emp in empleados:
    if "Mora" in emp.nombre:
        print("Empleado encontrado:", emp.nombre)
        p_min = _re.resolver_parametros_regla(
            'MIN_HORAS_MES_CALENDARIO', emp.nombre, "2026-07-01",
            reglas_servicio, emp.reglas, ajustes_reglas
        )
        print("Parametros de MIN_HORAS_MES_CALENDARIO:", p_min)
        min_h = p_min.get('min_horas', 144) if isinstance(p_min, dict) else 144
        print("min_h:", min_h)
        
        dias_lic = [d for d in range(31) if d in emp.dias_licencia]
        p_cred = _re.resolver_parametros_regla(
            'CREDITO_HORARIO_LICENCIA', emp.nombre, "2026-07-01",
            reglas_servicio, emp.reglas, ajustes_reglas
        )
        print("Parametros de CREDITO_HORARIO_LICENCIA:", p_cred)
        if _re.regla_existe(p_cred) and not _re.regla_suspendida(p_cred):
            horas_lic = int((p_cred.get('horas_por_semana', 36) / 7.0) * len(dias_lic) + 0.5)
        else:
            horas_lic = 0
        print("dias_lic:", dias_lic)
        print("horas_lic:", horas_lic)
        print("piso:", int((float(min_h) / 31) * 31 + 0.5))
