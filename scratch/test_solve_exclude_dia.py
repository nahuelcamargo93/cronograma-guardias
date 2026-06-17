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

# 1. Correct historical leveling date for PESO_EQUIDAD_FINDES_MENSUAL
if 'PESO_EQUIDAD_FINDES_MENSUAL' in reglas_servicio:
    reglas_servicio['PESO_EQUIDAD_FINDES_MENSUAL']['activo'] = 1
    reglas_servicio['PESO_EQUIDAD_FINDES_MENSUAL']['fecha_inicio'] = "2026-01-01"

# Load employees and rules
ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)
ajustes_servicio = db_queries.cargar_ajustes_reglas_servicio(fecha_inicio, fecha_fin, servicio_id)
ajustes_reglas['__servicio__'] = ajustes_servicio

original_cargar_reglas_servicio = db_queries.cargar_reglas_servicio
db_queries.cargar_reglas_servicio = lambda sid: reglas_servicio

try:
    empleados = obtener_empleados(servicio_id, fecha_inicio, DIAS_DEL_BLOQUE)
    
    # 2. Inject rule EXCLUIR_TURNOS Dia on weekdays for Jefe/Coordinadores in memory
    for emp in empleados:
        if emp.rol in ('Jefe', 'Coordinador'):
            t_excluir = "Dia_UTI" if emp.rol == "Jefe" or emp.nombre in ("Franco, Leandro", "Moyano, Fernando") else "Dia_UCO"
            # Get existing exclusions or create list
            excl = list(emp.reglas.get('EXCLUIR_TURNOS', []))
            # Append new exclusion for weekdays (0,1,2,3,4)
            excl.append({
                "turnos": [t_excluir],
                "dias": [0, 1, 2, 3, 4]
            })
            emp.reglas['EXCLUIR_TURNOS'] = excl
            print(f"Modificando EXCLUIR_TURNOS para {emp.nombre}: {t_excluir} excluido los días de semana (0-4)")

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
        force_assumptions=False
    )

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 100
    solver.parameters.num_search_workers = 4
    status = solver.Solve(modelo)

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        print("\n=== RESULTADOS SIMULADOS CON EXCLUSIÓN DE DIA EN DÍAS DE SEMANA (FINES DE SEMANA) ===")
        resultados = []
        dias_nombres = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        for dia in range(DIAS_DEL_BLOQUE):
            fecha_actual = fecha_inicio_dt + pd.Timedelta(days=dia)
            dia_semana = dias_nombres[fecha_actual.weekday()]
            es_finde = ((dia + offset_dia) % 7) >= 5 or dia in feriados_indices
            tipo_dia_res = "Finde_Feriado" if es_finde else "Semana"
            tipos_turnos = config_turnos.get(tipo_dia_res, {}).keys()
            for t in tipos_turnos:
                for emp in empleados:
                    nombre = emp.nombre
                    if (nombre, dia, t) in turnos and solver.Value(turnos[(nombre, dia, t)]) == 1:
                        resultados.append({
                            "Fecha": fecha_actual.strftime("%Y-%m-%d"),
                            "Dia_Semana": dia_semana,
                            "Turno": t,
                            "Personal": nombre
                        })
        df_res = pd.DataFrame(resultados)
        
        counts = {}
        for _, row in df_res.iterrows():
            dt = datetime.datetime.strptime(row['Fecha'], "%Y-%m-%d")
            if dt.weekday() in (5, 6):
                counts.setdefault(row['Personal'], []).append((row['Fecha'], row['Turno']))
        
        for emp in empleados:
            if emp.rol in ('Jefe', 'Coordinador'):
                w_shifts = counts.get(emp.nombre, [])
                total_hours = 0
                weekday_shifts = []
                for d in range(ctx.dias):
                    td = "Finde_Feriado" if ((d + ctx.offset_dia) % 7 >= 5 or d in feriados_indices) else "Semana"
                    for t in ctx.demanda_turnos.get(td, {}).keys():
                        if (emp.nombre, d, t) in turnos and solver.Value(turnos[(emp.nombre, d, t)]) == 1:
                            total_hours += ctx.turnos_dict[t].horas
                            if not ((d + ctx.offset_dia) % 7 >= 5 or d in feriados_indices):
                                weekday_shifts.append((d, t, ctx.turnos_dict[t].horas))
                print(f"\n{emp.nombre} ({emp.rol}): Findes: {len(w_shifts)}, Total Horas: {total_hours}")
                print("  Días de semana asignados:")
                for d, t, hs in weekday_shifts:
                    print(f"    - Día {d}: {t} ({hs} hs)")
                print("  Fines de semana asignados:")
                for f_str, turno in w_shifts:
                    print(f"    - {f_str} ({turno})")
    else:
        print("¡El modelo resultó INVIABLE al excluir turnos Dia en la semana!")

finally:
    pass
