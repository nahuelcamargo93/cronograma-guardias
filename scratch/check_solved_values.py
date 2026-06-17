import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import main
from database import queries as db_queries
from database import schema as db_schema
from database.data_loader import obtener_empleados, obtener_turnos
import datetime
from ortools.sat.python import cp_model

db_schema.inicializar_db()
db_queries.init_licencias()

servicio_id = 2
fecha_inicio = "2026-07-01"
fecha_fin = "2026-07-31"

fecha_inicio_dt = datetime.datetime.strptime(fecha_inicio, "%Y-%m-%d")
fecha_fin_dt    = datetime.datetime.strptime(fecha_fin,    "%Y-%m-%d")
total_dias = (fecha_fin_dt - fecha_inicio_dt).days + 1
DIAS_DEL_BLOQUE = total_dias
num_semanas     = (DIAS_DEL_BLOQUE + 6) // 7

feriados_indices = []
feriados_db = db_queries.obtener_feriados(fecha_inicio, fecha_fin)
for f_str in feriados_db:
    f_dt = datetime.datetime.strptime(f_str, "%Y-%m-%d")
    delta = (f_dt - fecha_inicio_dt).days
    if 0 <= delta < DIAS_DEL_BLOQUE:
        feriados_indices.append(delta)

config_turnos, metadata_turnos_raw, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
    servicio_id=servicio_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
)
reglas_servicio_db = db_queries.cargar_reglas_servicio(servicio_id)
ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)
ajustes_servicio = db_queries.cargar_ajustes_reglas_servicio(fecha_inicio, fecha_fin, servicio_id)
ajustes_reglas['__servicio__'] = ajustes_servicio

empleados = obtener_empleados(servicio_id, fecha_inicio, DIAS_DEL_BLOQUE)
turnos_dict = obtener_turnos(servicio_id)
historial_semana_previa = db_queries.cargar_guardias_previas(fecha_inicio, dias_atras=28, servicio_id=servicio_id)
offset_dia = fecha_inicio_dt.weekday()

modelo, turnos, flr_tracker, ctx = main.construir_modelo(
    empleados, config_turnos, turnos_dict, demanda_req, ajustes_db,
    DIAS_DEL_BLOQUE, feriados_indices, offset_dia, num_semanas,
    reglas_servicio=reglas_servicio_db,
    ajustes_reglas_personal=ajustes_reglas,
    historial_semana_previa=historial_semana_previa,
    servicio_id=servicio_id,
    fecha_inicio=fecha_inicio,
    fecha_fin=fecha_fin,
    modo_debug=False
)

solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 180
solver.parameters.num_search_workers = 8

# Activar las assumptions explícitamente en el script antes de resolver
from restricciones.cargador import activar_assumptions
activar_assumptions(modelo, ctx)

print("Resolviendo modelo...")
status = solver.Solve(modelo)

if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    print("¡Resuelto con éxito!")
    
    # 1. Buscar la assumption de ALBELO TANIA
    albelo_ass_var = None
    for name, var in ctx.assumptions:
        if name == "REG_FINDE_LARGO_REGLAMENTARIO__ALBELO_TANIA_cantidad":
            albelo_ass_var = var
            break
            
    if albelo_ass_var is not None:
        val_ass = solver.Value(albelo_ass_var)
        print(f"Valor de la assumption de ALBELO TANIA: {val_ass}")
    else:
        print("No se encontró la assumption para ALBELO TANIA en ctx.assumptions")
        
    # 2. Buscar opciones de FLR y ver sus valores
    print("\nOpciones de FLR para ALBELO TANIA:")
    albelo_flr_vars = []
    for (nombre, d), var in flr_tracker.items():
        if nombre == "ALBELO TANIA":
            albelo_flr_vars.append((d, var))
            
    for d, var in sorted(albelo_flr_vars):
        print(f" Día {d}: {var.Name()} = {solver.Value(var)}")
        
    print(f"Suma de todas las opciones de FLR de ALBELO TANIA: {sum(solver.Value(v) for _, v in albelo_flr_vars)}")

elif status == cp_model.INFEASIBLE:
    print("El solver devolvió INFEASIBLE. Buscando conflictos...")
    from restricciones.cargador import reportar_conflicto
    reportar_conflicto(solver, ctx)
else:
    print(f"El solver falló con estado: {status}")
