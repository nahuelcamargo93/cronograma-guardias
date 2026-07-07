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

    semanas_dt = [
        primer_lunes_dt - datetime.timedelta(days=21),
        primer_lunes_dt - datetime.timedelta(days=14),
        primer_lunes_dt - datetime.timedelta(days=7),
        primer_lunes_dt
    ]

    print("=== Historial de Familias (w0, w1, w2, w3) ===")
    for emp in empleados:
        hist_emp = historial_semana_previa.get(emp.nombre, [])
        seq_n = [1 if determinar_familia_ganadora(hist_emp, sd) == 'N' else 0 for sd in semanas_dt]
        seq_tn = [1 if determinar_familia_ganadora(hist_emp, sd) == 'TN' else 0 for sd in semanas_dt]
        
        # Verificar violaciones internas del historial (ventanas de tamaño 4 de los índices 0,1,2,3)
        # Solo hay una ventana de tamaño 4 en el historial: index 0,1,2,3.
        viol_n = sum(seq_n) > 1
        viol_tn = sum(seq_tn) > 1
        
        if viol_n or viol_tn:
            print(f"  {emp.nombre}:")
            if viol_n:
                print(f"    Violación N: seq={seq_n} (Suma={sum(seq_n)} > 1)")
            if viol_tn:
                print(f"    Violación TN: seq={seq_tn} (Suma={sum(seq_tn)} > 1)")

finally:
    conn.close()
