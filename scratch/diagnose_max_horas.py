import shutil
import sqlite3
import sys
import os
import importlib
import datetime

sys.path.append(os.path.abspath('.'))

from database import queries as db_queries
from database.data_loader import obtener_empleados, obtener_turnos
import rule_engine as _re
import scratch.diagnose_unsat as du

def run_test_scenario(desc, ignore_for_residentes=False, ignore_for_planta=False, ignore_for_name=None):
    db_queries.init_licencias()
    fecha_inicio = "2026-06-01"
    fecha_fin = "2026-06-30"
    fecha_inicio_dt = datetime.datetime.strptime(fecha_inicio, "%Y-%m-%d")
    fecha_fin_dt    = datetime.datetime.strptime(fecha_fin,    "%Y-%m-%d")
    total_dias = (fecha_fin_dt - fecha_inicio_dt).days + 1
    num_semanas = (total_dias + 6) // 7

    feriados_indices = []
    from data import FERIADOS
    for f_str in FERIADOS:
        f_dt = datetime.datetime.strptime(f_str, "%Y-%m-%d")
        delta = (f_dt - fecha_inicio_dt).days
        if 0 <= delta < total_dias:
            feriados_indices.append(delta)

    config_turnos, metadata_turnos_raw, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
        servicio_id=3, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
    )
    reglas_servicio_db = db_queries.cargar_reglas_servicio(3)
    ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)
    empleados = obtener_empleados(3, fecha_inicio, total_dias)
    turnos_dict = obtener_turnos(3)
    historial_semana_previa = db_queries.cargar_guardias_previas(fecha_inicio, dias_atras=28, servicio_id=3)
    offset_dia = fecha_inicio_dt.weekday()

    # Determine who to ignore rule for
    ignore_dict = {}
    for emp in empleados:
        ignore_rules = []
        is_res = (emp.rol == "Residente")
        if is_res and ignore_for_residentes:
            ignore_rules.append('MAX_HORAS_MES_CALENDARIO')
        if not is_res and ignore_for_planta:
            ignore_rules.append('MAX_HORAS_MES_CALENDARIO')
        if ignore_for_name and ignore_for_name in emp.nombre:
            ignore_rules.append('MAX_HORAS_MES_CALENDARIO')
        if ignore_rules:
            ignore_dict[emp.nombre] = ignore_rules

    args_modelo = (empleados, config_turnos, turnos_dict, demanda_req, ajustes_db, total_dias, feriados_indices, offset_dia, num_semanas, reglas_servicio_db, ajustes_reglas, historial_semana_previa, 3)

    modelo = du.construir_modelo_test(*args_modelo, reglas_a_ignorar_por_persona=ignore_dict)
    is_feasible = du.intentar_resolver(modelo)
    print(f"Scenario {desc}: Feasible = {is_feasible}")
    return is_feasible

print("Starting max_horas diagnosis...")
run_test_scenario("Base (No ignore)", ignore_for_residentes=False, ignore_for_planta=False)
run_test_scenario("Ignore for Residentes only", ignore_for_residentes=True, ignore_for_planta=False)
run_test_scenario("Ignore for Planta only", ignore_for_residentes=False, ignore_for_planta=True)

# Let's test individual Residentes if "Ignore for Residentes only" is True
print("\nTesting individual Residentes...")
for name in ["Arce Carolina", "Biscarra", "Matricadi", "Pacheco Celeste", "Palermo", "Villegas"]:
    run_test_scenario(f"Ignore for {name}", ignore_for_name=name)

# Let's test individual Planta doctors if "Ignore for Planta only" is True
print("\nTesting individual Planta...")
for name in ["Pregot", "Zeballos", "Aguilera Graciela", "Garcia Rodriguez", "Motta", "Navarro Suarez"]:
    run_test_scenario(f"Ignore for {name}", ignore_for_name=name)
