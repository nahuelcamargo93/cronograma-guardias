import sys
sys.path.append('.')
from datetime import date
import pandas as pd
from ortools.sat.python import cp_model
from database import queries as db_queries
from database.data_loader import obtener_empleados, obtener_turnos
import main
from restricciones.cargador import preparar_assumption
import importlib

# Patch cargar_y_ejecutar_todas so construir_modelo doesn't run all rules
main.cargar_y_ejecutar_todas = lambda m, c: None

servicio_id = 2
fecha_inicio = "2026-08-01"
fecha_fin = "2026-08-31"

# Force rule to HARD in DB
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

# Build base model
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
    force_assumptions=False
)

from restricciones.double import distancia_minima_tipo_semana
from restricciones.hard._utils import crear_y_vincular_variables_semanales

crear_y_vincular_variables_semanales(modelo, ctx)
preparar_assumption(modelo, ctx, 'DISTANCIA_MINIMA_TIPO_SEMANA')
distancia_minima_tipo_semana.apply(modelo, ctx)

# Force DISTANCIA_MINIMA_TIPO_SEMANA to 1
dist_var = None
for name, var in ctx.assumptions:
    if name == 'REG_DISTANCIA_MINIMA_TIPO_SEMANA':
        dist_var = var
        modelo.Add(var == 1)

status_names = {
    cp_model.OPTIMAL: "OPTIMAL",
    cp_model.FEASIBLE: "FEASIBLE",
    cp_model.INFEASIBLE: "INFEASIBLE",
    cp_model.UNKNOWN: "UNKNOWN"
}

def test_feasibility():
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 5 # 5 seconds
    status = solver.Solve(modelo)
    return status

status_base = test_feasibility()
print(f"Estado base + DISTANCIA: {status_names.get(status_base, 'UNKNOWN')}")
if status_base == cp_model.INFEASIBLE:
    print("[FAIL] El modelo base con DISTANCIA_MINIMA_TIPO_SEMANA e historial ya es INFEASIBLE por sí solo!")
    sys.exit(0)

from restricciones.hard import REGLAS_HARD
from restricciones.double import REGLAS_DOUBLE

all_other_rules = [r for r in REGLAS_HARD] + [r for r in REGLAS_DOUBLE if 'distancia_minima_tipo_semana' not in r]

conflicts = []
enabled_rules = []

# Clear assumptions from model
modelo.Proto().assumptions.clear()
active_lits = [dist_var.Index()]

for r_name in all_other_rules:
    modulo = importlib.import_module(r_name)
    codigo = r_name.rsplit('.', 1)[-1].upper()
    ctx.codigo_regla = codigo
    
    preparar_assumption(modelo, ctx, codigo)
    modulo.apply(modelo, ctx)
    ctx.current_assumption = None
    
    # Find the assumption var
    rule_var = None
    target_name = f"REG_{codigo}"
    for name, var in ctx.assumptions:
        if name == target_name:
            rule_var = var
            break
            
    if rule_var is not None:
        modelo.Proto().assumptions.clear()
        for lit in active_lits:
            modelo.Proto().assumptions.append(lit)
        modelo.Proto().assumptions.append(rule_var.Index())
        
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 5 # 5 seconds
        status = solver.Solve(modelo)
        status_name = status_names.get(status, "UNKNOWN")
        
        if status != cp_model.INFEASIBLE:
            active_lits.append(rule_var.Index())
            enabled_rules.append(codigo)
            print(f" -> Regla {codigo}: {status_name} (se mantiene activa)")
        else:
            conflicts.append(codigo)
            print(f" -> Regla {codigo}: {status_name} (se desactiva)")

print("\n================ RESULTADO DIAGNÓSTICO ==================")
print(f"Reglas que entraron en conflicto directo y se desactivaron:")
print(conflicts)
print("\nReglas que permanecieron activas:")
print(enabled_rules)
print("=========================================================\n")
conn.close()
