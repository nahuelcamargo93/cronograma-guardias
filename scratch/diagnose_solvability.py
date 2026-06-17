import sys
import os
import sqlite3
import datetime

# Asegurar que el directorio raíz está en sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main
from ortools.sat.python import cp_model
import database.queries as db_queries

def run_scenarios():
    conn = sqlite3.connect('cronograma_inteligente.db')
    print("Setting 492 to 'aprobado' temporarily...")
    conn.execute("UPDATE cronogramas SET estado = 'aprobado' WHERE id = 492")
    conn.commit()
    
    try:
        servicio_id = 3
        fecha_inicio = "2026-07-01"
        fecha_fin = "2026-07-31"

        # Initialize licencias in global query cache
        db_queries.init_licencias(servicio_id)

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

        # Helper solver function
        def solve_with_mods(reglas_mod, ignore_historial=False):
            hist = None if ignore_historial else historial_semana_previa
            
            modelo, turnos, flr_tracker, ctx = main.construir_modelo(
                empleados, config_turnos, turnos_dict, demanda_req, ajustes_db,
                dias_del_bloque, feriados_indices, offset_dia, num_semanas,
                reglas_servicio=reglas_mod,
                ajustes_reglas_personal=ajustes_reglas,
                historial_semana_previa=hist,
                servicio_id=servicio_id,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                modo_debug=False
            )
            
            solver = cp_model.CpSolver()
            solver.parameters.max_time_in_seconds = 20
            solver.parameters.num_search_workers = 4
            status = solver.Solve(modelo)
            return solver.StatusName(status)

        # Scenario 1: Baseline
        print("\n=== Escenario 1: Baseline (Con licencias y transición) ===")
        status = solve_with_mods(reglas_servicio_db)
        print("Status:", status)

        # Scenario 2: Baseline with historical transitions ignored
        print("\n=== Escenario 2: Sin transiciones históricas (historial=None) ===")
        status = solve_with_mods(reglas_servicio_db, ignore_historial=True)
        print("Status:", status)

        # Scenario 3: EXACTO_FINDE_Y_DIA disabled
        print("\n=== Escenario 3: EXACTO_FINDE_Y_DIA desactivado ===")
        reglas_mod_3 = reglas_servicio_db.copy()
        reglas_mod_3.pop('EXACTO_FINDE_Y_DIA', None)
        status = solve_with_mods(reglas_mod_3)
        print("Status:", status)

        # Scenario 4: EXACTO_FINDE_Y_DIA set to SOFT
        print("\n=== Escenario 4: EXACTO_FINDE_Y_DIA en modo SOFT ===")
        reglas_mod_4 = reglas_servicio_db.copy()
        if 'EXACTO_FINDE_Y_DIA' in reglas_mod_4:
            import copy
            params_dict = copy.deepcopy(reglas_mod_4['EXACTO_FINDE_Y_DIA'])
            params_dict['modo'] = 'SOFT'
            reglas_mod_4['EXACTO_FINDE_Y_DIA'] = params_dict
        status = solve_with_mods(reglas_mod_4)
        print("Status:", status)

        # Scenario 5: MIN_HORAS_MES_CALENDARIO disabled
        print("\n=== Escenario 5: MIN_HORAS_MES_CALENDARIO desactivado ===")
        reglas_mod_5 = reglas_servicio_db.copy()
        reglas_mod_5.pop('MIN_HORAS_MES_CALENDARIO', None)
        status = solve_with_mods(reglas_mod_5)
        print("Status:", status)

        # Scenario 6: MIN_HORAS_MES_CALENDARIO set to SOFT
        print("\n=== Escenario 6: MIN_HORAS_MES_CALENDARIO en modo SOFT ===")
        reglas_mod_6 = reglas_servicio_db.copy()
        if 'MIN_HORAS_MES_CALENDARIO' in reglas_mod_6:
            import copy
            params_dict = copy.deepcopy(reglas_mod_6['MIN_HORAS_MES_CALENDARIO'])
            params_dict['modo'] = 'SOFT'
            reglas_mod_6['MIN_HORAS_MES_CALENDARIO'] = params_dict
        status = solve_with_mods(reglas_mod_6)
        print("Status:", status)

    finally:
        print("\nRestoring 492 to 'borrador'...")
        conn.execute("UPDATE cronogramas SET estado = 'borrador' WHERE id = 492")
        conn.commit()
        conn.close()

if __name__ == "__main__":
    run_scenarios()
