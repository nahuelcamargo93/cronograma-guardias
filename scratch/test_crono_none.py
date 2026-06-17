import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main
from ortools.sat.python import cp_model
import database.queries as db_queries
import datetime

def test_crono_none():
    servicio_id = 1
    fecha_inicio = "2026-06-22"
    fecha_fin = "2026-07-31"
    crono_base_id = None # El valor activo real

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
    ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)
    ajustes_servicio = db_queries.cargar_ajustes_reglas_servicio(fecha_inicio, fecha_fin, servicio_id)
    ajustes_reglas['__servicio__'] = ajustes_servicio
    
    empleados = main.obtener_empleados(servicio_id, fecha_inicio, dias_del_bloque)
    turnos_dict = main.obtener_turnos(servicio_id)
    historial_semana_previa = db_queries.cargar_guardias_previas(fecha_inicio, dias_atras=28, servicio_id=servicio_id)
    offset_dia = fecha_inicio_dt.weekday()
    cronograma_base_guardias = None

    # Caso A: Con las nuevas reglas
    print("\n--- CASO A (Crono None) con nuevas reglas ---")
    modelo_a, turnos_a, flr_a, ctx_a = main.construir_modelo(
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
    solver_a = cp_model.CpSolver()
    solver_a.parameters.max_time_in_seconds = 30
    solver_a.parameters.num_search_workers = 4
    status_a = solver_a.Solve(modelo_a)
    print(f"Resultado Caso A (Crono None): {solver_a.StatusName(status_a)}")

    # Caso B: Sin las nuevas reglas
    print("\n--- CASO B (Crono None) sin nuevas reglas ---")
    reglas_servicio_b = reglas_servicio_db.copy()
    reglas_servicio_b.pop('CUMPLEANOS_LIBRE', None)
    reglas_servicio_b.pop('DIA_MADRE_PADRE_LIBRE', None)

    modelo_b, turnos_b, flr_b, ctx_b = main.construir_modelo(
        empleados, config_turnos, turnos_dict, demanda_req, ajustes_db,
        dias_del_bloque, feriados_indices, offset_dia, num_semanas,
        reglas_servicio=reglas_servicio_b,
        ajustes_reglas_personal=ajustes_reglas,
        historial_semana_previa=historial_semana_previa,
        servicio_id=servicio_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        modo_debug=False,
        cronograma_base_guardias=cronograma_base_guardias
    )
    solver_b = cp_model.CpSolver()
    solver_b.parameters.max_time_in_seconds = 30
    solver_b.parameters.num_search_workers = 4
    status_b = solver_b.Solve(modelo_b)
    print(f"Resultado Caso B (Crono None): {solver_b.StatusName(status_b)}")

if __name__ == "__main__":
    test_crono_none()
