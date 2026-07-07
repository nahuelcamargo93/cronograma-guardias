import sys
sys.path.insert(0, '.')
import sqlite3
from database.data_loader import obtener_empleados, obtener_turnos
import datetime
from datetime import date
import database.queries as db_queries
from restricciones.hard._utils import determinar_familia_ganadora

conn = sqlite3.connect('cronograma_inteligente.db')

try:
    servicio_id = 2
    fecha_inicio = "2026-08-01"
    dias_del_bloque = 31
    fecha_fin = "2026-08-31"

    config_turnos, metadata_turnos_raw, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
        servicio_id=servicio_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
    )
    empleados = obtener_empleados(servicio_id, fecha_inicio, dias_del_bloque)
    historial_semana_previa = db_queries.cargar_guardias_previas(fecha_inicio, dias_atras=28, servicio_id=servicio_id)

    fecha_inicio_dt = date.fromisoformat(fecha_inicio)
    primer_lunes_dt = fecha_inicio_dt - datetime.timedelta(days=fecha_inicio_dt.weekday())

    winners = {}
    for emp in empleados:
        hist_emp = historial_semana_previa.get(emp.nombre, [])
        winner = determinar_familia_ganadora(hist_emp, primer_lunes_dt)
        winners[emp.nombre] = winner

    print("=== Winners for Week 31 (July 27 - Aug 2) ===")
    from collections import Counter
    counts = Counter(winners.values())
    for fam, c in counts.items():
        print(f"Family {fam}: {c} professionals")

    # Let's print individual winners
    print("\nIndividual winners:")
    for name, w in sorted(winners.items()):
        print(f"  {name}: {w}")

finally:
    conn.close()
