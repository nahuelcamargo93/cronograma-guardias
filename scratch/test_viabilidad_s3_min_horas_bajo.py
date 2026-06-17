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

def test_resolve_low():
    servicio_id = 3
    fecha_inicio = "2026-07-01"
    fecha_fin = "2026-07-31"
    
    fecha_inicio_dt = datetime.datetime.strptime(fecha_inicio, "%Y-%m-%d")
    fecha_fin_dt    = datetime.datetime.strptime(fecha_fin,    "%Y-%m-%d")
    total_dias = (fecha_fin_dt - fecha_inicio_dt).days + 1
    
    # Cargar datos
    config_turnos, metadata_turnos_raw, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
        servicio_id=servicio_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
    )
    reglas_servicio_db = db_queries.cargar_reglas_servicio(servicio_id)
    
    # Forzar MIN_HORAS_MES_CALENDARIO a 96 horas
    if "MIN_HORAS_MES_CALENDARIO" in reglas_servicio_db:
        reglas_servicio_db["MIN_HORAS_MES_CALENDARIO"] = {"min_horas": 96}
        print("Forzando MIN_HORAS_MES_CALENDARIO del servicio a 96 horas")
    
    # Cargar ajustes
    ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)
    ajustes_servicio = db_queries.cargar_ajustes_reglas_servicio(fecha_inicio, fecha_fin, servicio_id)
    ajustes_reglas['__servicio__'] = ajustes_servicio
    
    empleados = obtener_empleados(servicio_id, fecha_inicio, total_dias)
    
    # Modificar también las reglas individuales de personal para que no superen las 96 horas
    for emp in empleados:
        if "MIN_HORAS_MES_CALENDARIO" in emp.reglas:
            # Si tiene regla individual, la bajamos a 96
            # En emp.reglas, la estructura es un dict de código de regla a lista de parámetros o dict
            p = emp.reglas["MIN_HORAS_MES_CALENDARIO"]
            if isinstance(p, list):
                for item in p:
                    if isinstance(item, dict) and item.get("min_horas", 0) > 96:
                        item["min_horas"] = 96
            elif isinstance(p, dict) and p.get("min_horas", 0) > 96:
                p["min_horas"] = 96
            print(f"Modificada regla individual de {emp.nombre} a 96 horas")
            
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
        force_assumptions=True
    )
    
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 15
    solver.parameters.num_search_workers = 4
    status = solver.Solve(modelo)
    
    print(f"Estado del Solver con piso de 96 horas: {solver.StatusName(status)}")
    
    if status == cp_model.INFEASIBLE:
        from restricciones.cargador import reportar_conflicto
        conflictos = reportar_conflicto(solver, ctx)
        print("Conflictos reportados (primeros 20):", conflictos[:20])
    elif status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        print("El modelo es viable con piso de 96 horas!")

if __name__ == "__main__":
    test_resolve_low()
