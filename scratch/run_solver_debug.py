import sys
import os

# Asegurar que el directorio raíz está en el path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import construir_modelo, resolver_modelo
from database import queries as db_queries
from database import schema as db_schema
from database.data_loader import obtener_empleados, obtener_turnos
import datetime
from ortools.sat.python import cp_model

def run_debug():
    servicio_id = 3
    fecha_inicio = "2026-07-01"
    fecha_fin = "2026-07-31"
    
    db_schema.inicializar_db()
    db_queries.init_licencias()
    
    fecha_inicio_dt = datetime.datetime.strptime(fecha_inicio, "%Y-%m-%d")
    fecha_fin_dt    = datetime.datetime.strptime(fecha_fin,    "%Y-%m-%d")
    
    total_dias = (fecha_fin_dt - fecha_inicio_dt).days + 1
    DIAS_DEL_BLOQUE = total_dias
    num_semanas     = (DIAS_DEL_BLOQUE + 6) // 7

    feriados_indices = []
    feriados_db = db_queries.obtener_feriados(fecha_inicio, fecha_fin)
    for f_str in feriados_db:
        f_dt = datetime.datetime.strptime(f_str, "%Y-%m-%d")
        delta = (f_dt - fecha_inicio_dt).days
        if 0 <= delta < DIAS_DEL_BLOQUE:
            feriados_indices.append(delta)

    config_turnos, metadata_turnos_raw, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
        servicio_id=servicio_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
    )
    reglas_servicio_db = db_queries.cargar_reglas_servicio(servicio_id)
    ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)
    
    ajustes_servicio = db_queries.cargar_ajustes_reglas_servicio(fecha_inicio, fecha_fin, servicio_id)
    ajustes_reglas['__servicio__'] = ajustes_servicio
    
    empleados = obtener_empleados(servicio_id, fecha_inicio, DIAS_DEL_BLOQUE)
    turnos_dict = obtener_turnos(servicio_id)
    
    historial_semana_previa = db_queries.cargar_guardias_previas(fecha_inicio, dias_atras=28, servicio_id=servicio_id)
    offset_dia = fecha_inicio_dt.weekday()
    
    # IMPORTANTE: Correr con modo_debug=False para obtener INFEASIBLE y ver el conflicto
    modelo, turnos, flr_tracker, ctx = construir_modelo(
        empleados, config_turnos, turnos_dict, demanda_req, ajustes_db,
        DIAS_DEL_BLOQUE, feriados_indices, offset_dia, num_semanas,
        reglas_servicio=reglas_servicio_db,
        ajustes_reglas_personal=ajustes_reglas,
        historial_semana_previa=historial_semana_previa,
        servicio_id=servicio_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        modo_debug=False
    )

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 100
    status = solver.Solve(modelo)
    
    if status == cp_model.INFEASIBLE:
        print("\n=== CONFLICTO DETECTADO POR EL SOLVER ===")
        from restricciones.cargador import reportar_conflicto
        reportar_conflicto(solver, ctx)
    else:
        print("\nEl modelo fue factible (o timeout/optimal) en esta configuración.")
        print("Status:", solver.StatusName(status))

if __name__ == "__main__":
    run_debug()
