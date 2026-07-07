import os
import sqlite3
import pandas as pd
from datetime import date, timedelta
from ortools.sat.python import cp_model
import sys

# Asegurar path de imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import main
from database import queries as db_queries
from database import schema as db_schema
from database.data_loader import obtener_empleados, obtener_turnos

def probar_escenario_reglas(excluir_reglas=None, sin_poletti=False, bajar_min_horas=False):
    db_schema.inicializar_db()
    db_queries.init_licencias(2)
    
    fecha_inicio = "2026-08-01"
    fecha_fin = "2026-08-31"
    
    fecha_inicio_dt = date.fromisoformat(fecha_inicio)
    fecha_fin_dt = date.fromisoformat(fecha_fin)
    dias_del_bloque = (fecha_fin_dt - fecha_inicio_dt).days + 1
    
    lunes_unicos = set()
    for d in range(dias_del_bloque):
        fecha_d = fecha_inicio_dt + timedelta(days=d)
        lunes = fecha_d - timedelta(days=fecha_d.weekday())
        lunes_unicos.add(lunes)
    num_semanas = len(lunes_unicos)

    feriados_indices = []
    feriados_db = db_queries.obtener_feriados(fecha_inicio, fecha_fin, servicio_id=2)
    for f_str in feriados_db:
        f_dt = date.fromisoformat(f_str)
        delta = (f_dt - fecha_inicio_dt).days
        if 0 <= delta < dias_del_bloque:
            feriados_indices.append(delta)

    config_turnos, metadata_turnos, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
        servicio_id=2, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
    )
    reglas_servicio_db = db_queries.cargar_reglas_servicio(2)
    ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)
    
    # Inyectar ajustes de reglas de servicio
    ajustes_servicio = db_queries.cargar_ajustes_reglas_servicio(fecha_inicio, fecha_fin, 2)
    ajustes_reglas['__servicio__'] = ajustes_servicio
    
    empleados = obtener_empleados(2, fecha_inicio, dias_del_bloque)
    turnos_dict = obtener_turnos(2)
    
    historial_semana_previa = db_queries.cargar_guardias_previas(fecha_inicio, dias_atras=28, servicio_id=2)
    offset_dia = fecha_inicio_dt.weekday()

    if sin_poletti:
        empleados = [e for e in empleados if "POLETTI" not in e.nombre]

    if bajar_min_horas:
        if 'MIN_HORAS_MES_CALENDARIO' in reglas_servicio_db:
            reglas_servicio_db['MIN_HORAS_MES_CALENDARIO']['min_horas'] = 0
            reglas_servicio_db['MIN_HORAS_MES_CALENDARIO']['minimo'] = 0
        if 'MAX_HORAS_MES_CALENDARIO' in reglas_servicio_db:
            reglas_servicio_db['MAX_HORAS_MES_CALENDARIO']['max_horas'] = 300

    # Guardar original
    original_cargar_y_ejecutar = main.cargar_y_ejecutar_todas
    
    excl_set = set(excluir_reglas or [])
    
    def cargar_y_ejecutar_con_exclusiones(modelo, ctx):
        from restricciones.hard import REGLAS_HARD
        from restricciones.double import REGLAS_DOUBLE
        
        modulos_filtrados_hard = [
            r for r in REGLAS_HARD
            if r.rsplit('.', 1)[-1].upper() not in excl_set
        ]
        modulos_filtrados_double = [
            r for r in REGLAS_DOUBLE
            if r.rsplit('.', 1)[-1].upper() not in excl_set
        ]
        
        from restricciones.hard._utils import crear_y_vincular_variables_semanales
        crear_y_vincular_variables_semanales(modelo, ctx)
        
        from restricciones.cargador import ejecutar_reglas, construir_objetivo_soft, activar_assumptions
        ejecutar_reglas(modelo, ctx, modulos_filtrados_hard)
        ejecutar_reglas(modelo, ctx, modulos_filtrados_double)
        
        construir_objetivo_soft(modelo, ctx)
        activar_assumptions(modelo, ctx, de_verdad=False)

    main.cargar_y_ejecutar_todas = cargar_y_ejecutar_con_exclusiones

    try:
        modelo, turnos, flr_tracker, ctx = main.construir_modelo(
            empleados, config_turnos, turnos_dict, demanda_req, ajustes_db,
            dias_del_bloque, feriados_indices, offset_dia, num_semanas,
            reglas_servicio=reglas_servicio_db,
            ajustes_reglas_personal=ajustes_reglas,
            historial_semana_previa=historial_semana_previa,
            servicio_id=2,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            modo_debug=False,
            force_assumptions=False,
            modo_debug_hard=False,
            exclusiones=None
        )
        
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 15
        solver.parameters.num_search_workers = 4
        
        status = solver.Solve(modelo)
        viable = status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
        return viable
    finally:
        main.cargar_y_ejecutar_todas = original_cargar_y_ejecutar

def correr():
    print("=== DISCRIMINANDO CONFLICTO DE HORAS (MENSUAL VS SEMANAL) ===")
    
    # Escenario A: Sin límites de horas mensuales (manteniendo semanal)
    v_mensual = probar_escenario_reglas(excluir_reglas=['MIN_HORAS_MES_CALENDARIO', 'MAX_HORAS_MES_CALENDARIO'])
    print(f"A. Sin límites de horas MENSUALES (MIN/MAX) -> Viable: {v_mensual}")
    
    # Escenario B: Sin límite de horas semanales (manteniendo mensuales)
    v_semanal = probar_escenario_reglas(excluir_reglas=['MAX_HORAS_SEMANA'])
    print(f"B. Sin límite de horas SEMANALES (MAX_HORAS_SEMANA) -> Viable: {v_semanal}")

if __name__ == "__main__":
    correr()
