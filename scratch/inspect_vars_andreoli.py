import sqlite3
import pandas as pd
import datetime
from datetime import date, timedelta
from ortools.sat.python import cp_model

from database import queries as db_queries
from database.data_loader import obtener_empleados, obtener_turnos
from main import construir_modelo

servicio_id = 2
fecha_inicio = "2026-08-01"
fecha_fin = "2026-08-31"

fecha_inicio_dt = date.fromisoformat(fecha_inicio)
fecha_fin_dt = date.fromisoformat(fecha_fin)
dias_del_bloque = (fecha_fin_dt - fecha_inicio_dt).days + 1

lunes_unicos = set()
for d in range(dias_del_bloque):
    fecha_d = fecha_inicio_dt + timedelta(days=d)
    lunes = fecha_d - timedelta(days=fecha_d.weekday())
    lunes_unicos.add(lunes)
num_semanas = len(lunes_unicos)

feriados_indices = []
feriados_db = db_queries.obtener_feriados(fecha_inicio, fecha_fin, servicio_id=servicio_id)
for f_str in feriados_db:
    f_dt = date.fromisoformat(f_str)
    delta = (f_dt - fecha_inicio_dt).days
    if 0 <= delta < dias_del_bloque:
        feriados_indices.append(delta)

config_turnos, turnos_info, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
    servicio_id=servicio_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
)
reglas_servicio = db_queries.cargar_reglas_servicio(servicio_id)
ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)
ajustes_servicio = db_queries.cargar_ajustes_reglas_servicio(fecha_inicio, fecha_fin, servicio_id)
ajustes_reglas['__servicio__'] = ajustes_servicio

empleados = obtener_empleados(servicio_id, fecha_inicio, dias_del_bloque)
turnos_dict = obtener_turnos(servicio_id)
historial_semana_previa = db_queries.cargar_guardias_previas(fecha_inicio, dias_atras=28, servicio_id=servicio_id)

offset_dia = fecha_inicio_dt.weekday()

modelo, turnos, flr_tracker, ctx = construir_modelo(
    empleados, config_turnos, turnos_dict, demanda_req, ajustes_db,
    dias_del_bloque, feriados_indices, offset_dia, num_semanas,
    reglas_servicio=reglas_servicio,
    ajustes_reglas_personal=ajustes_reglas,
    historial_semana_previa=historial_semana_previa,
    servicio_id=servicio_id,
    fecha_inicio=fecha_inicio,
    fecha_fin=fecha_fin,
    modo_debug=False,
    force_assumptions=False
)

solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 15
status = solver.Solve(modelo)

print(f"Estado de resolucion: {solver.StatusName(status)}")

target_emp_name = "ANDREOLI LUCIANA"
emp_obj = next(e for e in empleados if e.nombre == target_emp_name)

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    print(f"\n=== Variables FLR de {target_emp_name} ===")
    for (nombre, d), var in flr_tracker.items():
        if nombre == target_emp_name:
            val = solver.Value(var)
            fi = (fecha_inicio_dt + timedelta(days=d)).strftime("%Y-%m-%d")
            ff = (fecha_inicio_dt + timedelta(days=d+3)).strftime("%Y-%m-%d")
            print(f"  FLR en d={d} ({fi} -> {ff}) = {val}")

    print(f"\n=== Guardias Asignadas a {target_emp_name} por el Solver ===")
    for d in range(dias_del_bloque):
        for t in turnos_dict.keys():
            if (target_emp_name, d, t) in turnos:
                var = turnos[(target_emp_name, d, t)]
                if solver.Value(var) == 1:
                    fecha_str = (fecha_inicio_dt + timedelta(days=d)).isoformat()
                    print(f"  Dia {d} ({fecha_str}): {t}")
else:
    print("Modelo no resuelto o inviable")
