import sys
sys.path.insert(0, '.')
import sqlite3
from database.data_loader import obtener_empleados, obtener_turnos
import database.queries as db_queries
from restricciones.hard._utils import determinar_familia_ganadora
import datetime
from datetime import date
from ortools.sat.python import cp_model

conn = sqlite3.connect('cronograma_inteligente.db')

try:
    servicio_id = 2
    fecha_inicio = "2026-08-01"
    fecha_fin = "2026-08-31"
    dias_del_bloque = 31

    config_turnos, metadata_turnos_raw, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
        servicio_id=servicio_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
    )
    empleados = obtener_empleados(servicio_id, fecha_inicio, dias_del_bloque)
    
    historial_semana_previa = db_queries.cargar_guardias_previas(fecha_inicio, dias_atras=28, servicio_id=servicio_id)

    offset_dia = date.fromisoformat(fecha_inicio).weekday()

    # Construir el modelo CP-SAT para el fin de semana del 1 y 2 de agosto
    model = cp_model.CpModel()
    
    # 1. Crear variables de turno
    turnos_vars = {}
    for emp in empleados:
        primer_lunes_dt = date.fromisoformat(fecha_inicio) - datetime.timedelta(days=offset_dia)
        winner = determinar_familia_ganadora(historial_semana_previa.get(emp.nombre, []), primer_lunes_dt)
        emp.winner_w31 = winner
        
        hist_emp = historial_semana_previa.get(emp.nombre, [])
        week_shifts = [h for h in hist_emp if primer_lunes_dt <= date.fromisoformat(h['fecha']) < date.fromisoformat(fecha_inicio)]
        emp.prev_shifts_w31 = len(week_shifts)
        
        for d in [0, 1]:
            lista_turnos = config_turnos.keys()
            for t in lista_turnos:
                from restricciones.hard._utils import mapear_turno_a_familias
                fams_t = mapear_turno_a_familias(t)
                if not winner or not any(f in fams_t for f in [winner]):
                    continue
                v = model.NewBoolVar(f"t_{emp.nombre}_d{d}_{t}")
                turnos_vars[emp.nombre, d, t] = v

    print("=== INFO ===")
    print("Total variables created in turnos_vars:", len(turnos_vars))
    
    # Restricciones
    # 1. Un turno por día
    for emp in empleados:
        for d in [0, 1]:
            vars_dia = [v for (e, d_idx, t), v in turnos_vars.items() if e == emp.nombre and d_idx == d]
            model.Add(sum(vars_dia) <= 1)

    # 2. Carga semanal
    for emp in empleados:
        vars_sem = [v for (e, d_idx, t), v in turnos_vars.items() if e == emp.nombre]
        model.Add(sum(vars_sem) + emp.prev_shifts_w31 <= 5)

    # 3. Demanda para dia 0 y 1 con holguras
    slacks = {}
    for d in [0, 1]:
        for t in ['M', 'T', 'TN', 'N']:
            slack = model.NewIntVar(0, 7, f"slack_d{d}_{t}")
            slacks[d, t] = slack
            vars_t = [v for (e, d_idx, t_name), v in turnos_vars.items() if d_idx == d and t_name == t]
            model.Add(sum(vars_t) + slack >= 7)

    # Objetivo: minimizar la suma de las holguras
    model.Minimize(sum(slacks.values()))

    # Resolver
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 5
    status = solver.Solve(model)
    
    print("Status:", solver.StatusName(status))
    if status in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        print("Suma total de faltantes:", solver.ObjectiveValue())
        for d in [0, 1]:
            dia_str = "Sábado 1/8" if d == 0 else "Domingo 2/8"
            print(f"{dia_str}:")
            for t in ['M', 'T', 'TN', 'N']:
                val = solver.Value(slacks[d, t])
                assigned = sum(solver.Value(v) for (e, d_idx, t_name), v in turnos_vars.items() if d_idx == d and t_name == t)
                print(f"  Turno {t}: Asignados {assigned}/7 (Faltan {val})")

finally:
    conn.close()
