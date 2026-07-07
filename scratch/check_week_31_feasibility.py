import sys
sys.path.insert(0, '.')
import sqlite3
from database.data_loader import obtener_empleados, obtener_turnos
import database.queries as db_queries
from restricciones.hard._utils import determinar_familia_ganadora, is_finde
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
    reglas_servicio_db = db_queries.cargar_reglas_servicio(servicio_id)
    ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)
    
    ajustes_servicio = db_queries.cargar_ajustes_reglas_servicio(fecha_inicio, fecha_fin, servicio_id)
    ajustes_reglas['__servicio__'] = ajustes_servicio
    
    empleados = obtener_empleados(servicio_id, fecha_inicio, dias_del_bloque)
    turnos_dict = obtener_turnos(servicio_id)
    
    historial_semana_previa = db_queries.cargar_guardias_previas(fecha_inicio, dias_atras=28, servicio_id=servicio_id)

    # Cargar feriados
    fecha_inicio_dt = date.fromisoformat(fecha_inicio)
    fecha_fin_dt = date.fromisoformat(fecha_fin)
    feriados_indices = []
    feriados_db = db_queries.obtener_feriados(fecha_inicio, fecha_fin, servicio_id=servicio_id)
    for f_str in feriados_db:
        f_dt = datetime.datetime.strptime(f_str, "%Y-%m-%d")
        delta = (f_dt.date() - fecha_inicio_dt).days
        if 0 <= delta < dias_del_bloque:
            feriados_indices.append(delta)

    offset_dia = fecha_inicio_dt.weekday()

    # Construir el modelo CP-SAT para el fin de semana del 1 y 2 de agosto
    model = cp_model.CpModel()
    
    # 1. Crear variables de turno para el dia 0 (Sábado 1/8) y dia 1 (Domingo 2/8)
    turnos_vars = {}
    for emp in empleados:
        # Su ganador de la semana 31
        primer_lunes_dt = fecha_inicio_dt - datetime.timedelta(days=fecha_inicio_dt.weekday())
        winner = determinar_familia_ganadora(historial_semana_previa.get(emp.nombre, []), primer_lunes_dt)
        emp.winner_w31 = winner
        
        # Su cantidad de guardias previas trabajadas en la semana
        hist_emp = historial_semana_previa.get(emp.nombre, [])
        week_shifts = [h for h in hist_emp if primer_lunes_dt <= date.fromisoformat(h['fecha']) < fecha_inicio_dt]
        emp.prev_shifts_w31 = len(week_shifts)
        
        # Crear variables para dia 0 y 1
        for d in [0, 1]:
            # El turno debe ser de la familia ganadora
            tipo_dia = "Finde_Feriado"
            lista_turnos = config_turnos.keys()
            for t in lista_turnos:
                # Filtrar por familia
                from restricciones.hard._utils import mapear_turno_a_familias
                fams_t = mapear_turno_a_familias(t)
                if not winner or not any(f in fams_t for f in [winner]):
                    # Si no es de su familia ganadora, no puede hacer este turno
                    continue
                
                # Crear variable
                v = model.NewBoolVar(f"t_{emp.nombre}_d{d}_{t}")
                turnos_vars[emp.nombre, d, t] = v

    # Restricciones
    # 1. Un turno por día
    for emp in empleados:
        for d in [0, 1]:
            vars_dia = [v for (e, d_idx, t), v in turnos_vars.items() if e == emp.nombre and d_idx == d]
            model.Add(sum(vars_dia) <= 1)

    # 2. Carga semanal (esquema enfermería)
    # Para la semana 31, sum(vars) + prev_shifts <= 5
    for emp in empleados:
        vars_sem = [v for (e, d_idx, t), v in turnos_vars.items() if e == emp.nombre]
        model.Add(sum(vars_sem) + emp.prev_shifts_w31 <= 5)

    # 3. Demanda para dia 0 y 1
    # Cobertura de turnos (min)
    # M: 7, T: 7, TN: 7, N: 7
    # Note: no hay 12hs los findes por EXCLUIR_TURNOS, así que solo cubren con 6hs
    for d in [0, 1]:
        for t in ['M', 'T', 'TN', 'N']:
            vars_t = [v for (e, d_idx, t_name), v in turnos_vars.items() if d_idx == d and t_name == t]
            model.Add(sum(vars_t) >= 7)

    # Resolver
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 5
    status = solver.Solve(model)
    print("Status for Weekend 1/8 - 2/8:", solver.StatusName(status))

finally:
    conn.close()
