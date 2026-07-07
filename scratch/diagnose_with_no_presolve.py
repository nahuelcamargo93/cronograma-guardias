import sys
sys.path.append('.')
from datetime import date
import pandas as pd
from ortools.sat.python import cp_model
from database import queries as db_queries
from database.data_loader import obtener_empleados, obtener_turnos
import main

servicio_id = 2
fecha_inicio = "2026-08-01"
fecha_fin = "2026-08-31"

# Force the rule to HARD in the DB
import sqlite3
conn = sqlite3.connect('cronograma_inteligente.db')
c = conn.cursor()
c.execute("""
    UPDATE servicios_reglas 
    SET parametros_json = '{"modo": "HARD", "distancias": {"N": 3, "TN": 3}}', activo = 1
    WHERE servicio_id = 2 AND codigo_regla = 'DISTANCIA_MINIMA_TIPO_SEMANA'
""")
conn.commit()
conn.close()

# Cargar configuraciones
db_queries.init_licencias(servicio_id)
config_turnos, metadata_turnos_raw, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
    servicio_id=servicio_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
)
reglas_servicio_db = db_queries.cargar_reglas_servicio(servicio_id)
ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)
ajustes_servicio = db_queries.cargar_ajustes_reglas_servicio(fecha_inicio, fecha_fin, servicio_id)
ajustes_reglas['__servicio__'] = ajustes_servicio

empleados = obtener_empleados(servicio_id, fecha_inicio, 31)
turnos_dict = obtener_turnos(servicio_id)
historial_semana_previa = db_queries.cargar_guardias_previas(fecha_inicio, dias_atras=28, servicio_id=servicio_id)

fecha_inicio_dt = pd.to_datetime(fecha_inicio)
feriados_indices = [] 
feriados_db = db_queries.obtener_feriados(fecha_inicio, fecha_fin, servicio_id=servicio_id)
for f in feriados_db:
    f_dt = pd.to_datetime(f)
    diff = (f_dt - fecha_inicio_dt).days
    if 0 <= diff < 31:
        feriados_indices.append(diff)

offset_dia = fecha_inicio_dt.weekday()

# Build model with force_assumptions=True
modelo, turnos, flr_tracker, ctx = main.construir_modelo(
    empleados, config_turnos, turnos_dict, demanda_req, ajustes_db,
    31, feriados_indices, offset_dia, 5,
    reglas_servicio=reglas_servicio_db,
    ajustes_reglas_personal=ajustes_reglas,
    historial_semana_previa=historial_semana_previa,
    servicio_id=servicio_id,
    fecha_inicio=fecha_inicio,
    fecha_fin=fecha_fin,
    modo_debug=False,
    force_assumptions=True  # Force variables to be added via AddAssumptions
)

# Solve with presolve disabled!
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 60
solver.parameters.cp_model_presolve = False
solver.parameters.log_search_progress = True

print("Resolviendo con assumptions y presolve desactivado...")
status = solver.Solve(modelo)

if status == cp_model.INFEASIBLE:
    print("\n============================================================")
    print("Conflict detected! Sufficient assumptions for infeasibility:")
    conflict_vars = solver.SufficientAssumptionsForInfeasibility()
    
    # Map back to rule names
    conflict_names = []
    for lit in conflict_vars:
        # Find name in ctx.assumptions
        found = False
        for name, var in ctx.assumptions:
            # Check if index matches
            if var.Index() == lit or (lit < 0 and var.Index() == -lit - 1):
                conflict_names.append(name)
                found = True
                break
        if not found:
            conflict_names.append(f"VarIndex_{lit}")
            
    print(conflict_names)
    print("============================================================\n")
else:
    print(f"Solver status: {status}")

