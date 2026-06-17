import sqlite3
import json
import pandas as pd
import datetime
from datetime import date, timedelta
from ortools.sat.python import cp_model

from database import schema as db_schema
from database import queries as db_queries
from database.data_loader import obtener_empleados, obtener_turnos
from main import construir_modelo, resolver_modelo

servicio_id = 1
fecha_inicio = "2026-06-22"
fecha_fin = "2026-07-31"

db_schema.inicializar_db()
db_queries.init_licencias(servicio_id)

fecha_inicio_dt = datetime.datetime.strptime(fecha_inicio, "%Y-%m-%d")
fecha_fin_dt    = datetime.datetime.strptime(fecha_fin,    "%Y-%m-%d")
DIAS_DEL_BLOQUE = (fecha_fin_dt - fecha_inicio_dt).days + 1

lunes_unicos = set()
for d in range(DIAS_DEL_BLOQUE):
    fecha_d = fecha_inicio_dt + datetime.timedelta(days=d)
    lunes = fecha_d - datetime.timedelta(days=fecha_d.weekday())
    lunes_unicos.add(lunes.date())
num_semanas = len(lunes_unicos)

feriados_indices = []
feriados_db = db_queries.obtener_feriados(fecha_inicio, fecha_fin, servicio_id=servicio_id)
for f_str in feriados_db:
    f_dt = datetime.datetime.strptime(f_str, "%Y-%m-%d")
    delta = (f_dt - fecha_inicio_dt).days
    if 0 <= delta < DIAS_DEL_BLOQUE:
        feriados_indices.append(delta)

config_turnos, metadata_turnos_raw, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
    servicio_id=servicio_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
)

reglas_servicio = db_queries.cargar_reglas_servicio(servicio_id)

if 'PESO_EQUIDAD_FINDES_MENSUAL' in reglas_servicio:
    reglas_servicio['PESO_EQUIDAD_FINDES_MENSUAL']['activo'] = 1
    reglas_servicio['PESO_EQUIDAD_FINDES_MENSUAL']['fecha_inicio'] = "2026-01-01"

ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)
ajustes_servicio = db_queries.cargar_ajustes_reglas_servicio(fecha_inicio, fecha_fin, servicio_id)
ajustes_reglas['__servicio__'] = ajustes_servicio

original_cargar_reglas_servicio = db_queries.cargar_reglas_servicio
db_queries.cargar_reglas_servicio = lambda sid: reglas_servicio

try:
    empleados = obtener_empleados(servicio_id, fecha_inicio, DIAS_DEL_BLOQUE)
    
    # Exclude Dia on weekdays for Jefe/Coordinadores
    for emp in empleados:
        if emp.rol in ('Jefe', 'Coordinador'):
            t_excluir = "Dia_UTI" if emp.rol == "Jefe" or emp.nombre in ("Franco, Leandro", "Moyano, Fernando") else "Dia_UCO"
            excl = list(emp.reglas.get('EXCLUIR_TURNOS', []))
            excl.append({
                "turnos": [t_excluir],
                "dias": [0, 1, 2, 3, 4]
            })
            emp.reglas['EXCLUIR_TURNOS'] = excl

    turnos_dict = obtener_turnos(servicio_id)
    historial_semana_previa = db_queries.cargar_guardias_previas(fecha_inicio, dias_atras=28, servicio_id=servicio_id)

    offset_dia = fecha_inicio_dt.weekday()

    modelo, turnos, flr_tracker, ctx = construir_modelo(
        empleados, config_turnos, turnos_dict, demanda_req, ajustes_db,
        DIAS_DEL_BLOQUE, feriados_indices, offset_dia, num_semanas,
        reglas_servicio=reglas_servicio,
        ajustes_reglas_personal=ajustes_reglas,
        historial_semana_previa=historial_semana_previa,
        servicio_id=servicio_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        modo_debug=False,
        force_assumptions=True
    )

    # Force Toledo Andrea to work at least one weekend Dia_UCO shift
    toledo_vars = [
        turnos[(emp_nom, d, "Dia_UCO")]
        for (emp_nom, d, t), var in turnos.items()
        if emp_nom == "Toledo, Andrea" and t == "Dia_UCO" and ((d + offset_dia) % 7 >= 5 or d in feriados_indices)
    ]
    if toledo_vars:
        print(f"Forzando a Toledo, Andrea a cubrir al menos un fin de semana (de {len(toledo_vars)} opciones)...")
        modelo.Add(sum(toledo_vars) >= 1)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 100
    solver.parameters.num_search_workers = 4
    status = solver.Solve(modelo)

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        print("¡LOGRADO! Toledo, Andrea pudo trabajar el fin de semana sin conflictos.")
        # Find which day she works
        for d in range(DIAS_DEL_BLOQUE):
            if (Toledo_Andrea_d_Dia_UCO := ("Toledo, Andrea", d, "Dia_UCO")) in turnos:
                if solver.Value(turnos[Toledo_Andrea_d_Dia_UCO]) == 1:
                    print(f"  Trabaja el día {d} ({date.fromisoformat(fecha_inicio) + timedelta(days=d)})")
    elif status == cp_model.INFEASIBLE:
        print("Inviable al forzar el fin de semana.")
        from restricciones.cargador import reportar_conflicto
        reportar_conflicto(solver, ctx)
    else:
        print("Status desconocido:", status)

finally:
    pass
