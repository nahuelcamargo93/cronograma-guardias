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

    offset_dia = date.fromisoformat(fecha_inicio).weekday()
    primer_lunes_dt = date.fromisoformat(fecha_inicio) - datetime.timedelta(days=offset_dia)

    print("=== prev_shifts_w31 (number of guardias in transition week) ===")
    for emp in empleados:
        hist_emp = historial_semana_previa.get(emp.nombre, [])
        week_shifts = [h for h in hist_emp if primer_lunes_dt <= date.fromisoformat(h['fecha']) < date.fromisoformat(fecha_inicio)]
        
        # Ojo! ¿Cuántas de estas guardias tienen horas > 0?
        # En check_july_shifts.py vimos que había FCG que tenía horas = 0
        real_shifts = [h for h in week_shifts if h.get('horas', 0) > 0]
        
        print(f"  {emp.nombre}: total={len(week_shifts)} (real with hours={len(real_shifts)})")

finally:
    conn.close()
