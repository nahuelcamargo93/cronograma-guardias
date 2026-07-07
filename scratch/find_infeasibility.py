import sys
import os
import datetime
from datetime import date, timedelta
from ortools.sat.python import cp_model

# Ensure project root is in path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from main import construir_modelo
from database import queries as db_queries
from database import schema as db_schema
from database.data_loader import obtener_empleados, obtener_turnos

def main():
    servicio_id = 2
    fecha_inicio = "2026-08-01"
    fecha_fin = "2026-08-31"

    db_schema.inicializar_db()
    db_queries.init_licencias(servicio_id)
    
    fecha_inicio_dt = datetime.datetime.strptime(fecha_inicio, "%Y-%m-%d")
    fecha_fin_dt    = datetime.datetime.strptime(fecha_fin,    "%Y-%m-%d")
    total_dias = (fecha_fin_dt - fecha_inicio_dt).days + 1
    
    lunes_unicos = set()
    for d in range(total_dias):
        fecha_d = fecha_inicio_dt + datetime.timedelta(days=d)
        lunes = fecha_d - datetime.timedelta(days=fecha_d.weekday())
        lunes_unicos.add(lunes.date())
    num_semanas = len(lunes_unicos)

    feriados_indices = []
    feriados_db = db_queries.obtener_feriados(fecha_inicio, fecha_fin, servicio_id=servicio_id)
    for f_str in feriados_db:
        f_dt = datetime.datetime.strptime(f_str, "%Y-%m-%d")
        delta = (f_dt - fecha_inicio_dt).days
        if 0 <= delta < total_dias:
            feriados_indices.append(delta)

    config_turnos, turnos_info, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
        servicio_id=servicio_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
    )
    reglas_servicio_db = db_queries.cargar_reglas_servicio(servicio_id)
    ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)
    
    ajustes_servicio = db_queries.cargar_ajustes_reglas_servicio(fecha_inicio, fecha_fin, servicio_id)
    ajustes_reglas['__servicio__'] = ajustes_servicio
    
    empleados = obtener_empleados(servicio_id, fecha_inicio, total_dias)
    turnos_dict = obtener_turnos(servicio_id)
    
    historial_semana_previa = db_queries.cargar_guardias_previas(fecha_inicio, dias_atras=28, servicio_id=servicio_id)

    offset_dia = fecha_inicio_dt.weekday()

    # Get all rule names to exclude them
    from restricciones.hard import REGLAS_HARD
    from restricciones.double import REGLAS_DOUBLE
    codigos_reglas = []
    for r in REGLAS_HARD + REGLAS_DOUBLE:
        codigos_reglas.append(r.rsplit('.', 1)[-1].upper())
    
    exclusiones = set((cod, None) for cod in codigos_reglas)

    print("Building model with ALL logical rules excluded and force_assumptions=True...")
    modelo, turnos, flr_tracker, ctx = construir_modelo(
        empleados, config_turnos, turnos_dict, demanda_req, ajustes_db,
        total_dias, feriados_indices, offset_dia, num_semanas,
        reglas_servicio=reglas_servicio_db,
        ajustes_reglas_personal=ajustes_reglas,
        historial_semana_previa=historial_semana_previa,
        servicio_id=servicio_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        modo_debug=False,
        force_assumptions=True,
        exclusiones=exclusiones,
        asignaciones_fijas_eventuales={},
        asignaciones_fijas_recurrentes={},
        francos_forzados=set()
    )

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 30
    solver.parameters.log_search_progress = False
    
    print("Solving...")
    status = solver.Solve(modelo)
    
    if status == cp_model.INFEASIBLE:
        print("Model is INFEASIBLE.")
        from restricciones.cargador import reportar_conflicto
        reportar_conflicto(solver, ctx)
    elif status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        print("Model is FEASIBLE!")
    else:
        print(f"Solver status: {status}")

if __name__ == "__main__":
    main()
