import sqlite3
import json
import sys
import os
from datetime import datetime, date, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.data_loader import obtener_empleados, obtener_turnos
from database import queries as db_queries
import rule_engine as _re

conn = sqlite3.connect("cronograma_inteligente.db")
cur = conn.cursor()

# We simulate the mismatch:
# data.py FECHA_INICIO = "2026-06-01" (used inside rule resolver)
# but run dates are July: "2026-07-01" to "2026-07-31" (used for dias_del_bloque = 31)
fecha_inicio_data = "2026-06-01"
fecha_inicio_run = "2026-07-01"
fecha_fin_run = "2026-07-31"
servicio_id = 3

fecha_inicio_data_dt = date.fromisoformat(fecha_inicio_data)
fecha_inicio_run_dt = date.fromisoformat(fecha_inicio_run)
fecha_fin_run_dt = date.fromisoformat(fecha_fin_run)
dias_del_bloque = (fecha_fin_run_dt - fecha_inicio_run_dt).days + 1

from data import FERIADOS
feriados_indices = []
for f_str in FERIADOS:
    f_dt = date.fromisoformat(f_str)
    if fecha_inicio_run_dt <= f_dt <= fecha_fin_run_dt:
        feriados_indices.append((f_dt - fecha_inicio_run_dt).days)

offset_dia = fecha_inicio_run_dt.weekday()

empleados = obtener_empleados(servicio_id, fecha_inicio_run, dias_del_bloque)
turnos_dict = obtener_turnos(servicio_id)
reglas_servicio = db_queries.cargar_reglas_servicio(servicio_id)
ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio_run, fecha_fin_run)

# Note: when data.py is June, the adjustments loaded for rules resolution might also be from June,
# but let's check what adjustments are loaded if we pass FECHA_INICIO = "2026-06-01" to rule engine.

mapa_dias = {"lunes": 0, "martes": 1, "miercoles": 2, "jueves": 3, "viernes": 4, "sabado": 5, "domingo": 6}

print(f"Mismatch simulation: FECHA_INICIO in rule engine = {fecha_inicio_data}")
for emp in empleados:
    params = _re.resolver_parametros_regla(
        'EXACTO_FINDE_Y_DIA', emp.nombre, fecha_inicio_data,
        reglas_servicio, emp.reglas, ajustes_reglas
    )
    if not _re.regla_existe(params) or _re.regla_suspendida(params):
        print(f"{emp.nombre}: Rule not exists or suspended")
        continue

    dia_conf = params.get('dia_semana', 4)
    if isinstance(dia_conf, str):
        dia_str = dia_conf.lower().replace('é', 'e').replace('á', 'a').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
        dia_semana_target = mapa_dias.get(dia_str, 4)
    else:
        dia_semana_target = int(dia_conf)

    # Check tiene_asig_fija_en_dia using fecha_inicio_data!
    tiene_asig_fija_en_dia = False
    for d_check in range(dias_del_bloque):
        fecha_d_check = fecha_inicio_data_dt + timedelta(days=d_check)
        if fecha_d_check.weekday() != dia_semana_target:
            continue
        if d_check in emp.dias_licencia: # Note: this uses July licencias on June days indices, which is already wrong
            continue
        fecha_check_str = fecha_d_check.isoformat()
        p_asig = _re.resolver_parametros_regla('ASIGNACION_FIJA', emp.nombre, fecha_check_str, reglas_servicio, emp.reglas, ajustes_reglas)
        if _re.regla_existe(p_asig) and not _re.regla_suspendida(p_asig):
            tiene_asig_fija_en_dia = True
            print(f"{emp.nombre}: ASIGNACION_FIJA found on {fecha_check_str}")
            break

    if not tiene_asig_fija_en_dia:
        # Check target_d_real
        k_dia = 0
        for d in range(dias_del_bloque):
            fecha_d = fecha_inicio_data_dt + timedelta(days=d)
            if fecha_d.weekday() == dia_semana_target:
                # licencias check
                k_dia += 1
        
        mapping_dias = params.get('dias_por_disponibilidad')
        target_dias = mapping_dias.get(str(k_dia), mapping_dias.get(k_dia, 0)) if mapping_dias else 0
        print(f"{emp.nombre}: Friday rule active. k_dia={k_dia}, target_dias={target_dias}")

conn.close()
