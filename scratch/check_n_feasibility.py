import sys
sys.path.insert(0, '.')
import sqlite3
from database.data_loader import obtener_empleados
import database.queries as db_queries
from restricciones.hard._utils import determinar_familia_ganadora
import datetime
from datetime import date

conn = sqlite3.connect('cronograma_inteligente.db')

try:
    servicio_id = 2
    fecha_inicio = "2026-08-01"
    dias_del_bloque = 31

    empleados = obtener_empleados(servicio_id, fecha_inicio, dias_del_bloque)
    historial_semana_previa = db_queries.cargar_guardias_previas(fecha_inicio, dias_atras=28, servicio_id=servicio_id)

    fecha_inicio_dt = date.fromisoformat(fecha_inicio)
    primer_lunes_dt = fecha_inicio_dt - datetime.timedelta(days=fecha_inicio_dt.weekday())

    # Calcular ganadores para las 4 semanas anteriores
    # w0: 3 weeks ago (Jul 6 - Jul 12)
    # w1: 2 weeks ago (Jul 13 - Jul 19)
    # w2: 1 week ago (Jul 20 - Jul 26)
    # w3: transition week (Jul 27 - Aug 2)
    semanas_dt = [
        primer_lunes_dt - datetime.timedelta(days=21),
        primer_lunes_dt - datetime.timedelta(days=14),
        primer_lunes_dt - datetime.timedelta(days=7),
        primer_lunes_dt
    ]

    historial_n = {emp.nombre: [] for emp in empleados}
    historial_tn = {emp.nombre: [] for emp in empleados}

    for emp in empleados:
        hist_emp = historial_semana_previa.get(emp.nombre, [])
        for sem_dt in semanas_dt:
            winner = determinar_familia_ganadora(hist_emp, sem_dt)
            historial_n[emp.nombre].append(1 if winner == 'N' else 0)
            historial_tn[emp.nombre].append(1 if winner == 'TN' else 0)

    # Ahora para cada una de las semanas de planificación:
    # w4: Aug 3 - Aug 9
    # w5: Aug 10 - Aug 16
    # w6: Aug 17 - Aug 23
    # w7: Aug 24 - Aug 30
    # w8: Aug 31 - Sep 6
    
    # Vamos a simular las restricciones y ver quién puede trabajar en N y TN
    print("=== Análisis de Viabilidad para Noches (N) ===")
    for sem_plan in [4, 5, 6, 7, 8]:
        habilitados = 0
        for emp in empleados:
            seq = list(historial_n[emp.nombre])
            # Queremos ver si podemos poner un 1 en la semana sem_plan
            # Para esto, todas las ventanas de tamaño 4 que contengan a sem_plan deben sumar <= 1
            # Las ventanas correspondientes en la secuencia extendida:
            # seq tiene índices 0, 1, 2, 3 (historial).
            # Para sem_plan, agregamos variables (o asumimos 1 para este empleado y 0 para otros en la planificación).
            # Si ponemos 1 en sem_plan, ¿viola alguna ventana con el historial?
            # Por ejemplo, para sem_plan = 4 (índice 4):
            # Ventana [1, 2, 3, 4] debe sumar <= 1.
            # Ventana [2, 3, 4, 5] debe sumar <= 1 (si asumimos 1 en index 4, entonces index 5, 6, 7 deben ser 0).
            # En particular, para que index 4 pueda ser 1, la suma de [index 1, index 2, index 3] debe ser 0!
            # Para sem_plan = 5 (índice 5):
            # Ventana [2, 3, 4, 5] debe sumar <= 1. Si index 5 es 1, entonces index 2, 3, 4 deben ser 0.
            # En particular, index 2 y 3 (del historial) deben ser 0!
            # Para sem_plan = 6 (índice 6):
            # Ventana [3, 4, 5, 6] debe sumar <= 1. Si index 6 es 1, entonces index 3 (del historial) must be 0!
            
            puedo = True
            if sem_plan == 4:
                # Ventana [1, 2, 3] del historial debe ser todo 0
                if sum(seq[1:4]) > 0: puedo = False
            elif sem_plan == 5:
                # Ventana [2, 3] del historial debe ser todo 0
                if sum(seq[2:4]) > 0: puedo = False
            elif sem_plan == 6:
                # Ventana [3] del historial debe ser 0
                if seq[3] > 0: puedo = False
            
            if puedo:
                habilitados += 1
        print(f"Semana {sem_plan}: {habilitados} profesionales habilitados para N (min requerido: 10)")

    print("\n=== Análisis de Viabilidad para Tarde Noche (TN) ===")
    for sem_plan in [4, 5, 6, 7, 8]:
        habilitados = 0
        for emp in empleados:
            seq = list(historial_tn[emp.nombre])
            puedo = True
            if sem_plan == 4:
                if sum(seq[1:4]) > 0: puedo = False
            elif sem_plan == 5:
                if sum(seq[2:4]) > 0: puedo = False
            elif sem_plan == 6:
                if seq[3] > 0: puedo = False
            
            if puedo:
                habilitados += 1
        print(f"Semana {sem_plan}: {habilitados} profesionales habilitados para TN (min requerido: 10)")

finally:
    conn.close()
