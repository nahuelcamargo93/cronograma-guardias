import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main
from ortools.sat.python import cp_model
import database.queries as db_queries
import datetime

def test_soft_min_horas():
    servicio_id = 1
    fecha_inicio = "2026-06-22"
    fecha_fin = "2026-07-31"
    crono_base_id = 495

    # Cargar datos
    fecha_inicio_dt = datetime.datetime.strptime(fecha_inicio, "%Y-%m-%d")
    fecha_fin_dt = datetime.datetime.strptime(fecha_fin, "%Y-%m-%d")
    dias_del_bloque = (fecha_fin_dt - fecha_inicio_dt).days + 1

    lunes_unicos = set()
    for dia in range(dias_del_bloque):
        fecha_actual = fecha_inicio_dt + datetime.timedelta(days=dia)
        lunes = fecha_actual - datetime.timedelta(days=fecha_actual.weekday())
        lunes_unicos.add(lunes.date())
    num_semanas = len(lunes_unicos)

    feriados_indices = []
    feriados_db = db_queries.obtener_feriados(fecha_inicio, fecha_fin, servicio_id=servicio_id)
    for f_str in feriados_db:
        f_dt = datetime.datetime.strptime(f_str, "%Y-%m-%d")
        delta = (f_dt - fecha_inicio_dt).days
        if 0 <= delta < dias_del_bloque:
            feriados_indices.append(delta)

    config_turnos, metadata_turnos_raw, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
        servicio_id=servicio_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
    )
    reglas_servicio_db = db_queries.cargar_reglas_servicio(servicio_id)
    
    # Hacer SOFT la regla de MIN_HORAS_MES_CALENDARIO
    reglas_servicio_db['MIN_HORAS_MES_CALENDARIO'] = {
        "min_horas": 132,
        "modo": "SOFT",
        "peso_soft": 100000
    }
    
    ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)
    ajustes_servicio = db_queries.cargar_ajustes_reglas_servicio(fecha_inicio, fecha_fin, servicio_id)
    ajustes_reglas['__servicio__'] = ajustes_servicio
    
    empleados = main.obtener_empleados(servicio_id, fecha_inicio, dias_del_bloque)
    turnos_dict = main.obtener_turnos(servicio_id)
    historial_semana_previa = db_queries.cargar_guardias_previas(fecha_inicio, dias_atras=28, servicio_id=servicio_id)
    offset_dia = fecha_inicio_dt.weekday()
    cronograma_base_guardias = db_queries.obtener_guardias_cronograma(crono_base_id)

    print("\n--- CASO C: CON REGLAS DE CUMPLEAÑOS Y MIN_HORAS_MES_CALENDARIO COMO 'SOFT' ---")
    modelo, turnos, flr, ctx = main.construir_modelo(
        empleados, config_turnos, turnos_dict, demanda_req, ajustes_db,
        dias_del_bloque, feriados_indices, offset_dia, num_semanas,
        reglas_servicio=reglas_servicio_db,
        ajustes_reglas_personal=ajustes_reglas,
        historial_semana_previa=historial_semana_previa,
        servicio_id=servicio_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        modo_debug=False,
        cronograma_base_guardias=cronograma_base_guardias
    )
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 30
    solver.parameters.num_search_workers = 4
    status = solver.Solve(modelo)
    print(f"Resultado Caso C: {solver.StatusName(status)}")
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        print(f"Costo del objetivo: {solver.ObjectiveValue()}")

if __name__ == "__main__":
    test_soft_min_horas()
