import sys
sys.path.insert(0, '.')
import sqlite3
from database.data_loader import obtener_empleados
import database.queries as db_queries
from restricciones.hard._utils import determinar_familia_ganadora, mapear_turno_a_familias
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

    print("=== Shifts worked in July 27 - 31 ===")
    for emp in empleados:
        hist_emp = historial_semana_previa.get(emp.nombre, [])
        week_shifts = [h for h in hist_emp if primer_lunes_dt <= date.fromisoformat(h['fecha']) < fecha_inicio_dt]
        winner = determinar_familia_ganadora(hist_emp, primer_lunes_dt)
        print(f"  {emp.nombre} (winner: {winner}): {len(week_shifts)} shifts: {[h['turno'] for h in week_shifts]}")

finally:
    conn.close()
