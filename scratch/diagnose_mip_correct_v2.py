import sys
sys.path.insert(0, '.')
import sqlite3
from database.data_loader import obtener_empleados
import database.queries as db_queries
from restricciones.hard._utils import determinar_familia_ganadora
import datetime
from datetime import date
from ortools.sat.python import cp_model

conn = sqlite3.connect('cronograma_inteligente.db')

try:
    servicio_id = 2
    fecha_inicio = "2026-08-01"
    dias_del_bloque = 31

    empleados = obtener_empleados(servicio_id, fecha_inicio, dias_del_bloque)
    historial_semana_previa = db_queries.cargar_guardias_previas(fecha_inicio, dias_atras=28, servicio_id=servicio_id)

    fecha_inicio_dt = date.fromisoformat(fecha_inicio)
    primer_lunes_dt = fecha_inicio_dt - datetime.timedelta(days=fecha_inicio_dt.weekday())

    semanas_dt = [
        primer_lunes_dt - datetime.timedelta(days=21),
        primer_lunes_dt - datetime.timedelta(days=14),
        primer_lunes_dt - datetime.timedelta(days=7),
        primer_lunes_dt
    ]

    hist_n = {}
    hist_tn = {}
    for emp in empleados:
        hist_emp = historial_semana_previa.get(emp.nombre, [])
        hist_n[emp.nombre] = [1 if determinar_familia_ganadora(hist_emp, sd) == 'N' else 0 for sd in semanas_dt]
        hist_tn[emp.nombre] = [1 if determinar_familia_ganadora(hist_emp, sd) == 'TN' else 0 for sd in semanas_dt]

    model = cp_model.CpModel()
    familias = ['M', 'T', 'TN', 'N']
    x = {}
    
    # Fijar historial
    for emp in empleados:
        for sem in range(4):
            for fam in familias:
                val = 0
                if fam == 'N': val = hist_n[emp.nombre][sem]
                elif fam == 'TN': val = hist_tn[emp.nombre][sem]
                x[emp.nombre, sem, fam] = val

    # Crear variables para planificación
    for emp in empleados:
        for sem in range(4, 9):
            for fam in familias:
                x[emp.nombre, sem, fam] = model.NewBoolVar(f"x_{emp.nombre}_{sem}_{fam}")

    # Restricciones
    # 1. Mezcla semanal dura
    for emp in empleados:
        for sem in range(4, 9):
            model.Add(sum(x[emp.nombre, sem, fam] for fam in familias) <= 1)

    # 2. Distancia mínima tipo semana (N y TN) - Con salto de ventanas puramente históricas
    for emp in empleados:
        seq_n = [x[emp.nombre, sem, 'N'] for sem in range(9)]
        for i in range(len(seq_n) - 3):
            vars_ventana = seq_n[i:i+4]
            if all(isinstance(v, int) for v in vars_ventana):
                continue
            constantes = [v for v in vars_ventana if isinstance(v, int)]
            variables = [v for v in vars_ventana if not isinstance(v, int)]
            sum_const = sum(constantes)
            rhs = max(0, 1 - sum_const)
            model.Add(sum(variables) <= rhs)

        seq_tn = [x[emp.nombre, sem, 'TN'] for sem in range(9)]
        for i in range(len(seq_tn) - 3):
            vars_ventana = seq_tn[i:i+4]
            if all(isinstance(v, int) for v in vars_ventana):
                continue
            constantes = [v for v in vars_ventana if isinstance(v, int)]
            variables = [v for v in vars_ventana if not isinstance(v, int)]
            sum_const = sum(constantes)
            rhs = max(0, 1 - sum_const)
            model.Add(sum(variables) <= rhs)

    # 3. Cobertura con holguras
    slacks = {}
    demands = {'M': 10, 'T': 12, 'TN': 10, 'N': 10}
    
    for sem in range(4, 8):
        for fam in familias:
            req = demands[fam]
            slack = model.NewIntVar(0, req, f"slack_{sem}_{fam}")
            slacks[sem, fam] = slack
            model.Add(sum(x[emp.nombre, sem, fam] for emp in empleados) + slack >= req)

    # Objetivo: minimizar la suma de las holguras
    model.Minimize(sum(slacks.values()))

    # Resolver
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 5
    status = solver.Solve(model)
    
    print("Status:", solver.StatusName(status))
    if status in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        print("=== Diagnóstico de Holguras ===")
        print("Suma total de faltantes:", solver.ObjectiveValue())
        for sem in range(4, 8):
            print(f"Semana {sem}:")
            for fam in familias:
                val = solver.Value(slacks[sem, fam])
                assigned = sum(solver.Value(x[emp.nombre, sem, fam]) for emp in empleados)
                print(f"  Familia {fam}: Asignados {assigned}/{demands[fam]} (Faltan {val})")
    else:
        print("No se pudo resolver el modelo de diagnóstico!")

finally:
    conn.close()
