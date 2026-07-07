import sys
sys.path.append('.')
from datetime import date
import pandas as pd
from ortools.sat.python import cp_model
from database import queries as db_queries
from database.data_loader import obtener_empleados, obtener_turnos
import main
from restricciones.cargador import preparar_assumption, activar_assumptions
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
    31, feriados_indices, offset_dia, 6,
    reglas_servicio=reglas_servicio_db,
    ajustes_reglas_personal=ajustes_reglas,
    historial_semana_previa=historial_semana_previa,
    servicio_id=servicio_id,
    fecha_inicio=fecha_inicio,
    fecha_fin=fecha_fin,
    modo_debug=False,
    force_assumptions=False
)

# Apply exclusions
ctx.exclusiones = {
    ('DISTANCIA_MINIMA_TIPO_SEMANA', 'GUIÑAZU KARINA'),
    ('DISTANCIA_MINIMA_TIPO_SEMANA', 'PALANA GRACIELA'),
    ('DISTANCIA_MINIMA_TIPO_SEMANA', 'POLETTI NATALIA'),
    ('DISTANCIA_MINIMA_TIPO_SEMANA', 'RINALDINI IVANA'),
    ('DISTANCIA_MINIMA_TIPO_SEMANA', 'TULA DAIANA'),
    ('DISTANCIA_MINIMA_TIPO_SEMANA', 'GOMES STHEFANIA'),
    ('DISTANCIA_MINIMA_TIPO_SEMANA', 'SOSA NAHUEL'),
    ('DISTANCIA_MINIMA_TIPO_SEMANA', 'MAÑE LORENA'),
    ('DISTANCIA_MINIMA_TIPO_SEMANA', 'ECHENIQUE ROCIO')
}

forced_assumptions = set()

def test_feasibility(step_name):
    for name, var in ctx.assumptions:
        if name not in forced_assumptions:
            modelo.Add(var == 1)
            forced_assumptions.add(name)
            
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 1
    status = solver.Solve(modelo)
    viable = (status != cp_model.INFEASIBLE)
    print(f"Estado después de '{step_name}': {'VIABLE' if viable else 'INFEASIBLE'}")
    return viable

# Test base model
if not test_feasibility("construir_modelo base (solo variables/fijas)"):
    sys.exit(0)

# 1. Vincular variables semanales
from restricciones.hard._utils import crear_y_vincular_variables_semanales
crear_y_vincular_variables_semanales(modelo, ctx)
if not test_feasibility("Vincular variables semanales"):
    sys.exit(0)

# 2. Hard rules
from restricciones.hard import REGLAS_HARD
for r_name in REGLAS_HARD:
    modulo = importlib.import_module(r_name)
    codigo = r_name.rsplit('.', 1)[-1].upper()
    ctx.codigo_regla = codigo
    preparar_assumption(modelo, ctx, codigo)
    modulo.apply(modelo, ctx)
    ctx.current_assumption = None
    if not test_feasibility(f"Regla HARD {codigo}"):
        sys.exit(0)

# 3. Double rules
from restricciones.double import REGLAS_DOUBLE
for r_name in REGLAS_DOUBLE:
    modulo = importlib.import_module(r_name)
    codigo = r_name.rsplit('.', 1)[-1].upper()
    ctx.codigo_regla = codigo
    preparar_assumption(modelo, ctx, codigo)
    modulo.apply(modelo, ctx)
    ctx.current_assumption = None
    if not test_feasibility(f"Regla DOUBLE {codigo}"):
        sys.exit(0)

print("¡Todo viable!")
