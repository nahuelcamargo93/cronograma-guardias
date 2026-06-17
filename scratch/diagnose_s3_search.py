import os
import sys

# Asegurar que la raíz del proyecto está en el path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import datetime
from ortools.sat.python import cp_model
from database import queries as db_queries
from database.data_loader import obtener_empleados, obtener_turnos
import main as main_module

def probar_con_exclusiones(exclusiones):
    servicio_id = 3
    fecha_inicio = "2026-07-01"
    fecha_fin = "2026-07-31"
    
    fecha_inicio_dt = datetime.datetime.strptime(fecha_inicio, "%Y-%m-%d")
    fecha_fin_dt    = datetime.datetime.strptime(fecha_fin,    "%Y-%m-%d")
    total_dias = (fecha_fin_dt - fecha_inicio_dt).days + 1
    
    config_turnos, metadata_turnos_raw, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
        servicio_id=servicio_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
    )
    reglas_servicio_db = db_queries.cargar_reglas_servicio(servicio_id)
    ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)
    ajustes_servicio = db_queries.cargar_ajustes_reglas_servicio(fecha_inicio, fecha_fin, servicio_id)
    ajustes_reglas['__servicio__'] = ajustes_servicio
    
    empleados = obtener_empleados(servicio_id, fecha_inicio, total_dias)
    turnos_dict = obtener_turnos(servicio_id)
    
    feriados_indices = []
    feriados_db = db_queries.obtener_feriados(fecha_inicio, fecha_fin, servicio_id=servicio_id)
    for f_str in feriados_db:
        f_dt = datetime.datetime.strptime(f_str, "%Y-%m-%d")
        delta = (f_dt - fecha_inicio_dt).days
        if 0 <= delta < total_dias:
            feriados_indices.append(delta)
            
    offset_dia = fecha_inicio_dt.weekday()
    
    lunes_unicos = set()
    for d in range(total_dias):
        fecha_d = fecha_inicio_dt + datetime.timedelta(days=d)
        lunes = fecha_d - datetime.timedelta(days=fecha_d.weekday())
        lunes_unicos.add(lunes.date())
    num_semanas = len(lunes_unicos)

    modelo, turnos, flr_tracker, ctx = main_module.construir_modelo(
        empleados, config_turnos, turnos_dict, demanda_req, ajustes_db,
        total_dias, feriados_indices, offset_dia, num_semanas,
        reglas_servicio=reglas_servicio_db,
        ajustes_reglas_personal=ajustes_reglas,
        historial_semana_previa={},
        servicio_id=servicio_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        modo_debug=False,
        force_assumptions=False,
        exclusiones=exclusiones
    )
    
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 5
    solver.parameters.num_search_workers = 4
    status = solver.Solve(modelo)
    return solver.StatusName(status)

def main():
    # Probar diferentes combinaciones de exclusiones de reglas individuales
    # Formato: (codigo_regla, empleado) o (codigo_regla, None) para toda la regla
    
    tests = [
        ("Base (Sin exclusiones)", set()),
        ("Excluir SOLO_ASIGNACIONES_FIJAS (todos)", {("SOLO_ASIGNACIONES_FIJAS", None)}),
        ("Excluir EXCLUIR_TURNOS (todos)", {("EXCLUIR_TURNOS", None)}),
        ("Excluir MAX_TURNOS (todos)", {("MAX_TURNOS", None)}),
        ("Excluir EXCLUIR_TURNOS + MAX_TURNOS (todos)", {("EXCLUIR_TURNOS", None), ("MAX_TURNOS", None)}),
        ("Excluir EXCLUIR_TURNOS + SOLO_ASIGNACIONES_FIJAS (todos)", {("EXCLUIR_TURNOS", None), ("SOLO_ASIGNACIONES_FIJAS", None)}),
        ("Excluir MAX_TURNOS + SOLO_ASIGNACIONES_FIJAS (todos)", {("MAX_TURNOS", None), ("SOLO_ASIGNACIONES_FIJAS", None)}),
        ("Excluir EXCLUIR_TURNOS + MAX_TURNOS + SOLO_ASIGNACIONES_FIJAS (todos)", {
            ("EXCLUIR_TURNOS", None), ("MAX_TURNOS", None), ("SOLO_ASIGNACIONES_FIJAS", None)
        }),
    ]
    
    print("Iniciando pruebas de viabilidad sistemáticas...")
    for desc, excl in tests:
        res = probar_con_exclusiones(excl)
        print(f"Prueba: {desc} -> Resultado: {res}")

if __name__ == "__main__":
    main()
