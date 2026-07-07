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

    # Cargar historial
    hist_n = {}
    hist_tn = {}
    for emp in empleados:
        hist_emp = historial_semana_previa.get(emp.nombre, [])
        hist_n[emp.nombre] = [1 if determinar_familia_ganadora(hist_emp, sd) == 'N' else 0 for sd in semanas_dt]
        hist_tn[emp.nombre] = [1 if determinar_familia_ganadora(hist_emp, sd) == 'TN' else 0 for sd in semanas_dt]

    model = cp_model.CpModel()
    
    # Variables de decisión: x[emp, sem, fam]
    # sem: 0, 1, 2, 3 (historial), 4, 5, 6, 7, 8 (planificación)
    familias = ['M', 'T', 'TN', 'N']
    x = {}
    
    # Fijar historial
    for emp in empleados:
        for sem in range(4):
            for fam in familias:
                val = 0
                if fam == 'N': val = hist_n[emp.nombre][sem]
                elif fam == 'TN': val = hist_tn[emp.nombre][sem]
                # Para M y T del historial no restringimos ya que no tienen distancias mínimas en el servicio
                x[emp.nombre, sem, fam] = val

    # Crear variables para planificación
    for emp in empleados:
        for sem in range(4, 9):
            for fam in familias:
                x[emp.nombre, sem, fam] = model.NewBoolVar(f"x_{emp.nombre}_{sem}_{fam}")

    # Restricciones
    # 1. Mezcla semanal dura: a lo sumo una familia por semana
    for emp in empleados:
        for sem in range(4, 9):
            model.Add(sum(x[emp.nombre, sem, fam] for fam in familias) <= 1)

    # 2. Distancia mínima tipo semana (N y TN)
    # Ventanas de tamaño 4 (w = 4)
    # Para N:
    for emp in empleados:
        # Secuencia completa de N de 9 semanas (0 a 8)
        seq_n = [x[emp.nombre, sem, 'N'] for sem in range(9)]
        for i in range(len(seq_n) - 3):
            model.Add(sum(seq_n[i:i+4]) <= 1)

    # Para TN:
    for emp in empleados:
        seq_tn = [x[emp.nombre, sem, 'TN'] for sem in range(9)]
        for i in range(len(seq_tn) - 3):
            model.Add(sum(seq_tn[i:i+4]) <= 1)

    # 3. Cobertura: cada semana de planificación (4, 5, 6, 7, 8) debe tener suficientes profesionales de cada tipo
    # Para simplificar, asumimos que requerimos:
    # M: 10, T: 12, TN: 10, N: 10
    # Nota: la semana 8 es la última (solo tiene 1 día en agosto, pero el modelo la planifica completa).
    # Vamos a usar el mínimo requerido para semanas normales (4, 5, 6, 7)
    for sem in range(4, 8):
        model.Add(sum(x[emp.nombre, sem, 'M'] for emp in empleados) >= 10)
        model.Add(sum(x[emp.nombre, sem, 'T'] for emp in empleados) >= 12)
        model.Add(sum(x[emp.nombre, sem, 'TN'] for emp in empleados) >= 10)
        model.Add(sum(x[emp.nombre, sem, 'N'] for emp in empleados) >= 10)

    # Resolver
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 5
    status = solver.Solve(model)
    
    if status == cp_model.FEASIBLE or status == cp_model.OPTIMAL:
        print("¡El modelo simplificado de familias es VIABLE!")
    else:
        print("¡El modelo simplificado de familias es INVIABLE!")

finally:
    conn.close()
