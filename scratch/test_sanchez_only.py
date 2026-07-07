import sys
import os
from datetime import date, timedelta
from ortools.sat.python import cp_model

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import main
from database import queries as db_queries
from database import schema as db_schema
from database.data_loader import obtener_empleados, obtener_turnos

def test_sanchez_only():
    db_schema.inicializar_db()
    db_queries.init_licencias(3)
    
    fecha_inicio = "2026-07-01"
    fecha_fin = "2026-07-31"
    fecha_inicio_dt = date.fromisoformat(fecha_inicio)
    fecha_fin_dt = date.fromisoformat(fecha_fin)
    dias_del_bloque = (fecha_fin_dt - fecha_inicio_dt).days + 1
    offset_dia = fecha_inicio_dt.weekday()
    
    lunes_unicos = set()
    for d in range(dias_del_bloque):
        fecha_d = fecha_inicio_dt + timedelta(days=d)
        lunes = fecha_d - timedelta(days=fecha_d.weekday())
        lunes_unicos.add(lunes)
    num_semanas = len(lunes_unicos)

    feriados_indices = []
    feriados_db = db_queries.obtener_feriados(fecha_inicio, fecha_fin, servicio_id=3)
    for f_str in feriados_db:
        f_dt = date.fromisoformat(f_str)
        delta = (f_dt - fecha_inicio_dt).days
        if 0 <= delta < dias_del_bloque:
            feriados_indices.append(delta)

    config_turnos, turnos_info, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
        servicio_id=3, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
    )
    reglas_servicio_db = db_queries.cargar_reglas_servicio(3)
    ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)
    ajustes_servicio = db_queries.cargar_ajustes_reglas_servicio(fecha_inicio, fecha_fin, 3)
    ajustes_reglas['__servicio__'] = ajustes_servicio
    
    empleados = obtener_empleados(3, fecha_inicio, dias_del_bloque)
    
    # Desactivar restricciones de todos los empleados MENOS Sánchez Reinoso
    for emp in empleados:
        if emp.nombre != "Sánchez Reinoso, Ana Belén":
            emp.dias_licencia = set()
            emp.reglas = {}
            
    # También limpiar de ajustes de reglas de personal para otros empleados
    ajustes_reglas_filtrados = {}
    for k, v in ajustes_reglas.items():
        if k == "Sánchez Reinoso, Ana Belén" or k == "__servicio__":
            ajustes_reglas_filtrados[k] = v
            
    turnos_dict = obtener_turnos(3)
    historial_semana_previa = db_queries.cargar_guardias_previas(fecha_inicio, dias_atras=28, servicio_id=3)

    modelo, turnos, flr_tracker, ctx = main.construir_modelo(
        empleados, config_turnos, turnos_dict, demanda_req, ajustes_db,
        dias_del_bloque, feriados_indices, offset_dia, num_semanas,
        reglas_servicio=reglas_servicio_db,
        ajustes_reglas_personal=ajustes_reglas_filtrados,
        historial_semana_previa=historial_semana_previa,
        servicio_id=3,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        modo_debug=False,
        force_assumptions=True,
        cronograma_base_guardias=None,
        lock_fecha_inicio=None,
        lock_fecha_fin=None
    )
    
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 30
    solver.parameters.num_search_workers = 4
    solver.parameters.log_search_progress = True
    
    status = solver.Solve(modelo)
    if status == cp_model.INFEASIBLE:
        print("\n--- Sánchez Reinoso solo es INVIABLE ---")
        from restricciones.cargador import reportar_conflicto
        reportar_conflicto(solver, ctx)
    else:
        print(f"\n--- Sánchez Reinoso solo es VIABLE (status: {status}) ---")

if __name__ == '__main__':
    test_sanchez_only()
