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

    model = cp_model.CpModel()
    
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

    # Restricciones
    for emp in empleados:
        for d in [0, 1]:
            vars_dia = [v for (e, d_idx, t), v in turnos_vars.items() if e == emp.nombre and d_idx == d]
            model.Add(sum(vars_dia) <= 1)

    for emp in empleados:
        vars_sem = [v for (e, d_idx, t), v in turnos_vars.items() if e == emp.nombre]
        model.Add(sum(vars_sem) + emp.prev_shifts_w31 <= 5)

    # Forzar a Alcaraz Francisco a trabajar en M el Sábado 1/8
    emp_name = 'ALCARAZ FRANCISO'
    var_to_force = turnos_vars.get((emp_name, 0, 'M'))
    if var_to_force is not None:
        print(f"Forzando {emp_name} en M el Sábado 1/8...")
        model.Add(var_to_force == 1)
    else:
        print(f"No se encontró la variable para {emp_name} en M!")

    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    print("Status after forcing:", solver.StatusName(status))

finally:
    conn.close()
