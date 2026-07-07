import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import datetime
from datetime import date, timedelta
import sqlite3
import pandas as pd
from database import queries as db_queries
from database import schema as db_schema
from database.data_loader import obtener_empleados, obtener_turnos
from main import construir_modelo, resolver_modelo
from ortools.sat.python import cp_model

def run_experiment():
    print("=== INICIANDO EXPERIMENTO 3: MEZCLA_SEMANAL_DURA (HARD), MANEJO_FINDES (OFF), force_assumptions=False ===")
    servicio_id = 2
    fecha_inicio = "2026-08-01"
    fecha_fin = "2026-08-31"
    
    fecha_inicio_dt = datetime.datetime.strptime(fecha_inicio, "%Y-%m-%d")
    fecha_fin_dt    = datetime.datetime.strptime(fecha_fin,    "%Y-%m-%d")
    total_dias = (fecha_fin_dt - fecha_inicio_dt).days + 1
    
    # Cargar datos normales
    config_turnos, turnos_info_raw, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
        servicio_id=servicio_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
    )
    reglas_servicio_db = db_queries.cargar_reglas_servicio(servicio_id)
    ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)
    
    # DESACTIVAR MANEJO_FINDES
    if 'MANEJO_FINDES' in reglas_servicio_db:
        del reglas_servicio_db['MANEJO_FINDES']
    
    # Asegurar que MEZCLA_SEMANAL_DURA esté activa
    if 'MEZCLA_SEMANAL_DURA' not in reglas_servicio_db:
        reglas_servicio_db['MEZCLA_SEMANAL_DURA'] = {}
            
    empleados = obtener_empleados(servicio_id, fecha_inicio, total_dias)
    turnos_dict = obtener_turnos(servicio_id)
    historial_semana_previa = db_queries.cargar_guardias_previas(fecha_inicio, dias_atras=28, servicio_id=servicio_id)
    
    # Calcular feriados
    feriados_indices = []
    feriados_db = db_queries.obtener_feriados(fecha_inicio, fecha_fin, servicio_id=servicio_id)
    for f_str in feriados_db:
        f_dt = datetime.datetime.strptime(f_str, "%Y-%m-%d")
        delta = (f_dt - fecha_inicio_dt).days
        if 0 <= delta < total_dias:
            feriados_indices.append(delta)

    # MODIFICACIÓN EXPERIMENTAL: Bajar la demanda de fin de semana a 1 vacante
    print("\nModificando temporalmente la demanda de fin de semana a 1 vacante...")
    for dem in demanda_req.get("Finde_Feriado", []):
        d_c_id = dem["id"]
        rango = ("2026-08-01", "2026-08-02")
        ajustes_db.setdefault(rango, []).append({
            "demanda_config_id": d_c_id,
            "cantidad_min": 1,
            "cantidad_max": 1,
            "dias_override": None
        })

    # Mapear semanas y construir
    lunes_unicos = set()
    for d in range(total_dias):
        fecha_d = fecha_inicio_dt + datetime.timedelta(days=d)
        lunes = fecha_d - datetime.timedelta(days=fecha_d.weekday())
        lunes_unicos.add(lunes.date())
    num_semanas = len(lunes_unicos)
    offset_dia = fecha_inicio_dt.weekday()

    # Construimos el modelo sin assumptions
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
        force_assumptions=False # PERMITIR SIMPLIFICACIONES EN PRESOLVE
    )
    
    # Resolver
    print("Iniciando la resolución con simplificaciones del presolve...")
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 20 # Suficiente con simplificación
    solver.parameters.num_search_workers = 4
    
    status = solver.Solve(modelo)
    
    print("\n" + "="*50)
    print("=== RESULTADO DEL EXPERIMENTO 3 ===")
    print("="*50)
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print("ESTADO: FEASIBLE / OPTIMAL")
        print("¡El modelo es VIABLE! Confirmado 100%.")
    elif status == cp_model.INFEASIBLE:
        print("ESTADO: INFEASIBLE")
        print("El modelo sigue siendo INVIABLE.")
    else:
        print(f"ESTADO DESCONOCIDO: {status}")
    print("="*50 + "\n")

if __name__ == "__main__":
    run_experiment()
