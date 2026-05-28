import shutil
import sqlite3
import sys
import os
import importlib

sys.path.append(os.path.abspath('.'))

db_original = "cronograma_inteligente.db"
db_copy = "cronograma_inteligente_test.db"

def try_scenario(desc, adjustments_to_deactivate):
    # Copy fresh db
    shutil.copyfile(db_original, db_copy)
    
    conn = sqlite3.connect(db_copy)
    cur = conn.cursor()
    
    # Deactivate the specified adjustments
    for adj_id in adjustments_to_deactivate:
        cur.execute("UPDATE personal_reglas_ajustes SET activo = 0 WHERE id = ?", (adj_id,))
    conn.commit()
    conn.close()
    
    # Patch connection.py DB_PATH
    import database.connection as db_conn
    db_conn.DB_PATH = os.path.abspath(db_copy)
    
    # Reload queries to use patched DB path
    import database.queries as db_queries
    importlib.reload(db_queries)
    import database.data_loader as dl
    importlib.reload(dl)
    import scratch.diagnose_unsat as du
    importlib.reload(du)
    
    # Check feasibility
    fecha_inicio = "2026-06-01"
    fecha_fin = "2026-06-30"
    fecha_inicio_dt = datetime.datetime.strptime(fecha_inicio, "%Y-%m-%d")
    fecha_fin_dt    = datetime.datetime.strptime(fecha_fin,    "%Y-%m-%d")
    total_dias = (fecha_fin_dt - fecha_inicio_dt).days + 1
    num_semanas = (total_dias + 6) // 7

    feriados_indices = []
    from data import FERIADOS
    for f_str in FERIADOS:
        f_dt = datetime.datetime.strptime(f_str, "%Y-%m-%d")
        delta = (f_dt - fecha_inicio_dt).days
        if 0 <= delta < total_dias:
            feriados_indices.append(delta)

    config_turnos, metadata_turnos_raw, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
        servicio_id=3, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
    )
    reglas_servicio_db = db_queries.cargar_reglas_servicio(3)
    ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)
    empleados = dl.obtener_empleados(3, fecha_inicio, total_dias)
    turnos_dict = dl.obtener_turnos(3)
    historial_semana_previa = db_queries.cargar_guardias_previas(fecha_inicio, dias_atras=28, servicio_id=3)
    offset_dia = fecha_inicio_dt.weekday()

    args_modelo = (empleados, config_turnos, turnos_dict, demanda_req, ajustes_db, total_dias, feriados_indices, offset_dia, num_semanas, reglas_servicio_db, ajustes_reglas, historial_semana_previa, 3)

    modelo = du.construir_modelo_test(*args_modelo)
    is_feasible = du-intentar_resolver(modelo) # wait, I made a typo, it should be du.intentar_resolver(modelo)
    
    # Clean up file
    try:
        os.remove(db_copy)
    except:
        pass
        
    return is_feasible

import datetime
import scratch.diagnose_unsat as du

# Fix typo in try_scenario's call:
def try_scenario_fixed(desc, adjustments_to_deactivate):
    if os.path.exists(db_copy):
        try: os.remove(db_copy)
        except: pass
    shutil.copyfile(db_original, db_copy)
    
    conn = sqlite3.connect(db_copy)
    cur = conn.cursor()
    for adj_id in adjustments_to_deactivate:
        cur.execute("UPDATE personal_reglas_ajustes SET activo = 0 WHERE id = ?", (adj_id,))
    conn.commit()
    conn.close()
    
    import database.connection as db_conn
    db_conn.DB_PATH = os.path.abspath(db_copy)
    import database.queries as db_queries
    importlib.reload(db_queries)
    import database.data_loader as dl
    importlib.reload(dl)
    import scratch.diagnose_unsat as du
    importlib.reload(du)
    
    fecha_inicio = "2026-06-01"
    fecha_fin = "2026-06-30"
    fecha_inicio_dt = datetime.datetime.strptime(fecha_inicio, "%Y-%m-%d")
    fecha_fin_dt    = datetime.datetime.strptime(fecha_fin,    "%Y-%m-%d")
    total_dias = (fecha_fin_dt - fecha_inicio_dt).days + 1
    num_semanas = (total_dias + 6) // 7

    feriados_indices = []
    from data import FERIADOS
    for f_str in FERIADOS:
        f_dt = datetime.datetime.strptime(f_str, "%Y-%m-%d")
        delta = (f_dt - fecha_inicio_dt).days
        if 0 <= delta < total_dias:
            feriados_indices.append(delta)

    config_turnos, metadata_turnos_raw, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
        servicio_id=3, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
    )
    reglas_servicio_db = db_queries.cargar_reglas_servicio(3)
    ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)
    empleados = dl.obtener_empleados(3, fecha_inicio, total_dias)
    turnos_dict = dl.obtener_turnos(3)
    historial_semana_previa = db_queries.cargar_guardias_previas(fecha_inicio, dias_atras=28, servicio_id=3)
    offset_dia = fecha_inicio_dt.weekday()

    args_modelo = (empleados, config_turnos, turnos_dict, demanda_req, ajustes_db, total_dias, feriados_indices, offset_dia, num_semanas, reglas_servicio_db, ajustes_reglas, historial_semana_previa, 3)

    modelo = du.construir_modelo_test(*args_modelo)
    is_feasible = du.intentar_resolver(modelo)
    
    conn = sqlite3.connect(db_copy)
    conn.close() # just to be safe
    return is_feasible

# Test scenarios:
# 1364: Biscarra Franco Forzado June 13-15
# 1365: Villegas Oliva Franco Forzado June 13-15
# 1363: Pacheco Celeste Franco Forzado June 13-15
# 1362: Arce Carolina Franco Forzado June 13-15

print("Scenario: Deactivating Biscarra Franco Forzado (ID 1364)...")
res = try_scenario_fixed("Biscarra", [1364])
print(f"Result: Feasible = {res}")

print("\nScenario: Deactivating Villegas Oliva Franco Forzado (ID 1365)...")
res = try_scenario_fixed("Villegas", [1365])
print(f"Result: Feasible = {res}")

print("\nScenario: Deactivating Pacheco Celeste Franco Forzado (ID 1363)...")
res = try_scenario_fixed("Pacheco", [1363])
print(f"Result: Feasible = {res}")

print("\nScenario: Deactivating BOTH Biscarra (1364) and Villegas (1365)...")
res = try_scenario_fixed("Biscarra+Villegas", [1364, 1365])
print(f"Result: Feasible = {res}")

if os.path.exists(db_copy):
    try: os.remove(db_copy)
    except: pass
