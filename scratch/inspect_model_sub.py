import sqlite3
import json
import sys
import os
from datetime import datetime, date, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.data_loader import obtener_empleados, obtener_turnos
from database import queries as db_queries
from main import construir_modelo
from data import FERIADOS, FECHA_INICIO, FECHA_FIN, SERVICIO_ID
import rule_engine as _re

print("FECHA_INICIO in data.py:", FECHA_INICIO)
print("FECHA_FIN in data.py:", FECHA_FIN)

fecha_inicio = FECHA_INICIO
fecha_fin = FECHA_FIN
servicio_id = SERVICIO_ID

fecha_inicio_dt = date.fromisoformat(fecha_inicio)
fecha_fin_dt = date.fromisoformat(fecha_fin)
dias_del_bloque = (fecha_fin_dt - fecha_inicio_dt).days + 1
num_semanas = (dias_del_bloque + 6) // 7

feriados_indices = []
for f_str in FERIADOS:
    f_dt = date.fromisoformat(f_str)
    if fecha_inicio_dt <= f_dt <= fecha_fin_dt:
        feriados_indices.append((f_dt - fecha_inicio_dt).days)

offset_dia = fecha_inicio_dt.weekday()

config_turnos, metadata_turnos_raw, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
    servicio_id=servicio_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
)
reglas_servicio_db = db_queries.cargar_reglas_servicio(servicio_id)
ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)

ajustes_servicio = db_queries.cargar_ajustes_reglas_servicio(fecha_inicio, fecha_fin, servicio_id)
ajustes_reglas['__servicio__'] = ajustes_servicio

empleados = obtener_empleados(servicio_id, fecha_inicio, dias_del_bloque)
turnos_dict = obtener_turnos(servicio_id)
historial_semana_previa = db_queries.cargar_guardias_previas(fecha_inicio, dias_atras=28, servicio_id=servicio_id)

print("\n--- CHECKING EXACTO_FINDE_Y_DIA BEFORE MODEL BUILD ---")
for emp in empleados:
    params = _re.resolver_parametros_regla(
        'EXACTO_FINDE_Y_DIA', emp.nombre, FECHA_INICIO,
        reglas_servicio_db, emp.reglas, ajustes_reglas
    )
    exists = _re.regla_existe(params)
    suspended = _re.regla_suspendida(params)
    print(f"Emp: {emp.nombre} | Exists: {exists} | Suspended: {suspended} | Params: {params}")

modelo, turnos_vars, flr_tracker, vars_turno_sem = construir_modelo(
    empleados, config_turnos, turnos_dict, demanda_req, ajustes_db,
    dias_del_bloque, feriados_indices, offset_dia, num_semanas,
    reglas_servicio=reglas_servicio_db,
    ajustes_reglas_personal=ajustes_reglas,
    historial_semana_previa=historial_semana_previa,
    servicio_id=servicio_id
)

print("\n--- INSPECTING CONSTRAINTS ---")
proto = modelo.Proto()
count = 0
for c in proto.constraints:
    c_str = str(c)
    if "traba_dia_exacto" in c_str or "traba_f_exacto" in c_str or "exacto_finde" in c_str:
        print(c_str)
        count += 1
print(f"Total matching constraints: {count}")
