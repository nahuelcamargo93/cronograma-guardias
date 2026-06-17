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
# Ensure MANEJO_FINDES is active and uses historical start date 2026-01-01
reglas_servicio['MANEJO_FINDES'] = {
    "activo": 1,
    "modo": "SOFT",
    "peso_soft": 10000,
    "por_disponibilidad": {
        "5": {"flr": 0, "completos": 2, "medios": 1},
        "4": {"flr": 0, "completos": 1, "medios": 1},
        "3": {"flr": 0, "completos": 1, "medios": 1},
        "2": {"flr": 0, "completos": 1, "medios": 1},
        "1": {"flr": 0, "completos": 1, "medios": 0}
    },
    "nivelacion_historica": {
        "activo": True,
        "tipo": "ANUAL",
        "fecha_inicio": "2026-01-01"
    }
}
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

    # Let's run a quick solve
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 60
    solver.parameters.num_search_workers = 4
    status = solver.Solve(modelo)

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        print("=== DETALLE DE VARIABLES MANEJO_FINDES PARA SIMULACIÓN ===")
        # We need to manually calculate k_disp, targets, hist_c, etc. like manejo_findes.py does
        import rule_engine as _re
        from restricciones.hard._utils import is_finde
        
        # 1. Agrupar findes por semana
        findes = {}
        for d in range(ctx.dias):
            wd = (fecha_inicio_dt + timedelta(days=d)).weekday()
            if wd in (5, 6):
                fd = fecha_inicio_dt + timedelta(days=d)
                lunes = (fd - timedelta(days=wd)).isoformat()
                findes.setdefault(lunes, []).append((d, wd))

        # We need to compute completos_historicos and medios_historicos exactly like manejo_findes.py
        # Since it's identical to our previous query script, let's pull them:
        c_hist_dict = {"Franco, Leandro": 1, "Moyano, Fernando": 2, "Toledo, Andrea": 0, "Garcia, Luciano": 0}
        m_hist_dict = {"Franco, Leandro": 7, "Moyano, Fernando": 5, "Toledo, Andrea": 8, "Garcia, Luciano": 7}

        for emp in ctx.empleados:
            if emp.nombre not in c_hist_dict:
                continue # Only check chiefs and coordinators
                
            params = _re.resolver_parametros_regla(
                'MANEJO_FINDES', emp.nombre, fecha_inicio,
                ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
            )
            
            def _disponible(d_idx):
                if d_idx in emp.dias_licencia:
                    return False
                p = _re.resolver_parametros_regla(
                    'FRANCO_FORZADO', emp.nombre,
                    (fecha_inicio_dt + timedelta(days=d_idx)).isoformat(),
                    ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
                )
                return not (_re.regla_existe(p) and not _re.regla_suspendida(p))

            k_disp = sum(1 for lunes, dias_f in findes.items() if any(_disponible(d) for d, _ in dias_f))
            conf_disp = params.get('por_disponibilidad', {}).get(str(k_disp), {})
            target_c = conf_disp.get('completos', 0)
            target_m = conf_disp.get('medios', 0)
            
            c_hist = c_hist_dict.get(emp.nombre, 0)
            m_hist = m_hist_dict.get(emp.nombre, 0)
            
            # Let's count how many completed and half weekends were ACTUALLY assigned
            assigned_c = 0
            assigned_m = 0
            for lunes, dias_f in findes.items():
                d_sat = next((d for d, w in dias_f if w == 5), None)
                d_sun = next((d for d, w in dias_f if w == 6), None)
                if d_sat is None or d_sun is None:
                    continue
                
                # Check if worked sat
                sat_worked = False
                for t in ctx.demanda_turnos.get("Finde_Feriado", {}).keys():
                    if (emp.nombre, d_sat, t) in ctx.turnos:
                        if solver.Value(ctx.turnos[(emp.nombre, d_sat, t)]) == 1:
                            sat_worked = True
                            
                # Check if worked sun
                sun_worked = False
                for t in ctx.demanda_turnos.get("Finde_Feriado", {}).keys():
                    if (emp.nombre, d_sun, t) in ctx.turnos:
                        if solver.Value(ctx.turnos[(emp.nombre, d_sun, t)]) == 1:
                            sun_worked = True
                            
                if sat_worked and sun_worked:
                    assigned_c += 1
                elif sat_worked or sun_worked:
                    assigned_m += 1
            
            print(f"\nEmpleado: {emp.nombre} ({emp.rol})")
            print(f"  k_disp (disponibilidad findes): {k_disp}")
            print(f"  Target completos (mes): {target_c}, Target medios (mes): {target_m}")
            print(f"  Histórico completos: {c_hist}, Histórico medios: {m_hist}")
            print(f"  Asignados completos en este mes: {assigned_c}, Asignados medios: {assigned_m}")
            
            # Let's check the violations
            viol_c_over = max(0, assigned_c + c_hist - (target_c + c_hist))
            viol_c_under = max(0, (target_c + c_hist) - (assigned_c + c_hist))
            viol_m_over = max(0, assigned_m + m_hist - (target_m + m_hist))
            viol_m_under = max(0, (target_m + m_hist) - (assigned_m + m_hist))
            
            print(f"  Violación completos (under): {viol_c_under}, Violación completos (over): {viol_c_over}")
            print(f"  Violación medios (under): {viol_m_under}, Violación medios (over): {viol_m_over}")
            print(f"  Penalización teórica pagada: {(viol_c_under + viol_c_over + viol_m_under + viol_m_over) * 10000}")
            
            # Let's count weekday hours and shifts
            weekday_shifts = []
            for d in range(ctx.dias):
                if not is_finde(d, ctx.offset_dia, ctx.feriados):
                    for t in ctx.demanda_turnos.get("Semana", {}).keys():
                        if (emp.nombre, d, t) in ctx.turnos and solver.Value(ctx.turnos[(emp.nombre, d, t)]) == 1:
                            weekday_shifts.append((d, t))
            print(f"  Días de semana asignados: {len(weekday_shifts)}")
            for d, t in weekday_shifts:
                print(f"    - Día {d} ({t})")
            
            # Print total July hours
            total_july_hours = 0
            for d in range(ctx.dias):
                # July 2026 starts at day index 9 (since June 22 is 0, July 1 is 9)
                if d >= 9:
                    td = "Finde_Feriado" if is_finde(d, ctx.offset_dia, ctx.feriados) else "Semana"
                    for t in ctx.demanda_turnos.get(td, {}).keys():
                        if (emp.nombre, d, t) in ctx.turnos and solver.Value(ctx.turnos[(emp.nombre, d, t)]) == 1:
                            total_july_hours += ctx.turnos_dict[t].horas
            print(f"  Total horas julio: {total_july_hours} (Límite: 144 hs)")

    else:
        print("Model infeasible")

finally:
    db_queries.cargar_reglas_servicio = original_cargar_reglas_servicio
conn.close()
