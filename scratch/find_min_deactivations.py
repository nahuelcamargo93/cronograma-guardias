import datetime
from datetime import date, timedelta
import itertools
import json
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from ortools.sat.python import cp_model
from database import queries as db_queries
from database import schema as db_schema
from database.data_loader import obtener_empleados, obtener_turnos
from data import FECHA_INICIO, FECHA_FIN, FERIADOS, SERVICIO_ID
import rule_engine as _re
from debug_imposibilidad import construir_modelo_test

def intentar_resolver(modelo):
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 1.0  # Feasibility check is instant without soft rules
    solver.parameters.log_search_progress = False
    status = solver.Solve(modelo)
    return status == cp_model.OPTIMAL or status == cp_model.FEASIBLE

def evaluar_combinacion(comb, args_modelo, reglas_ignorar_global):
    reglas_a_ignorar_por_persona = {nombre: ['EXACTO_FINDE_Y_DIA'] for nombre in comb}
    modelo_test = construir_modelo_test(*args_modelo, reglas_a_ignorar=reglas_ignorar_global, reglas_a_ignorar_por_persona=reglas_a_ignorar_por_persona)
    res = intentar_resolver(modelo_test)
    return comb, res

def run_analysis():
    print("=== INICIANDO ANÁLISIS DE MÍNIMAS DESACTIVACIONES (PARALELO) ===", flush=True)
    print(f"Servicio ID: {SERVICIO_ID} | {FECHA_INICIO} a {FECHA_FIN}", flush=True)
    
    db_schema.inicializar_db()
    db_queries.init_licencias()
    
    fecha_inicio_dt = datetime.datetime.strptime(FECHA_INICIO, "%Y-%m-%d")
    fecha_fin_dt    = datetime.datetime.strptime(FECHA_FIN,    "%Y-%m-%d")
    total_dias = (fecha_fin_dt - fecha_inicio_dt).days + 1
    num_semanas = (total_dias + 6) // 7

    feriados_indices = []
    for f_str in FERIADOS:
        f_dt = datetime.datetime.strptime(f_str, "%Y-%m-%d")
        delta = (f_dt - fecha_inicio_dt).days
        if 0 <= delta < total_dias:
            feriados_indices.append(delta)

    config_turnos, metadata_turnos_raw, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
        servicio_id=SERVICIO_ID, fecha_inicio=FECHA_INICIO, fecha_fin=FECHA_FIN
    )
    reglas_servicio_db = db_queries.cargar_reglas_servicio(SERVICIO_ID)
    ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(FECHA_INICIO, FECHA_FIN)
    
    ajustes_servicio = db_queries.cargar_ajustes_reglas_servicio(FECHA_INICIO, FECHA_FIN, SERVICIO_ID)
    ajustes_reglas['__servicio__'] = ajustes_servicio
    
    empleados = obtener_empleados(SERVICIO_ID, FECHA_INICIO, total_dias)
    turnos_dict = obtener_turnos(SERVICIO_ID)
    historial_semana_previa = db_queries.cargar_guardias_previas(FECHA_INICIO, dias_atras=28, servicio_id=SERVICIO_ID)
    offset_dia = fecha_inicio_dt.weekday()

    # Excluiremos REGLAS_BLANDAS para acelerar la factibilidad a milisegundos
    reglas_ignorar_global = ['REGLAS_BLANDAS']

    args_modelo = (empleados, config_turnos, turnos_dict, demanda_req, ajustes_db, total_dias, feriados_indices, offset_dia, num_semanas, reglas_servicio_db, ajustes_reglas, historial_semana_previa, SERVICIO_ID)

    # Check if base model is feasible
    print("Probando modelo base (ignorando reglas blandas)...", flush=True)
    modelo_base = construir_modelo_test(*args_modelo, reglas_a_ignorar=reglas_ignorar_global)
    if intentar_resolver(modelo_base):
        print("[OK] El modelo base ya es viable! No hace falta desactivar la regla para nadie.", flush=True)
        return

    # List of professionals
    nombres_profesionales = [emp.nombre for emp in empleados]
    print(f"Profesionales a evaluar ({len(nombres_profesionales)}):", flush=True)
    for idx, nombre in enumerate(nombres_profesionales, 1):
        print(f"  {idx}. {nombre}", flush=True)

    # Search combinations using ProcessPoolExecutor
    with ProcessPoolExecutor() as executor:
        for k in range(1, len(nombres_profesionales) + 1):
            print(f"\nProbando desactivar combinaciones de tamaño {k}...", flush=True)
            t_start = time.time()
            
            # Generar todas las tareas
            combinations = list(itertools.combinations(nombres_profesionales, k))
            total_tasks = len(combinations)
            print(f"  Enviando {total_tasks} combinaciones al pool de procesos...", flush=True)
            
            futures = {
                executor.submit(evaluar_combinacion, comb, args_modelo, reglas_ignorar_global): comb
                for comb in combinations
            }
            
            soluciones = []
            completed = 0
            for future in as_completed(futures):
                comb = futures[future]
                completed += 1
                try:
                    comb, res = future.result()
                    if res:
                        soluciones.append(comb)
                        print(f"  [VIABLE] {comb}", flush=True)
                except Exception as exc:
                    print(f"  [ERROR] {comb} generó una excepción: {exc}", flush=True)
                
                if completed % 50 == 0 or completed == total_tasks:
                    print(f"  Progress: {completed}/{total_tasks} ({completed/total_tasks*100:.1f}%)", flush=True)
            
            t_duration = time.time() - t_start
            print(f"Ronda de tamaño {k} completada en {t_duration:.2f} segundos.", flush=True)
            
            if soluciones:
                print(f"\n[ÉXITO] Se encontraron soluciones viables desactivando exactamente {k} persona(s)!", flush=True)
                print("Combinaciones viables encontradas:", flush=True)
                for idx, s in enumerate(soluciones, 1):
                    print(f"  Opción {idx}: {', '.join(s)}", flush=True)
                break
        else:
            print("\n[FAIL] No se encontró ninguna combinación viable, incluso desactivando a todos.", flush=True)

if __name__ == '__main__':
    run_analysis()
