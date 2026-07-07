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

status_names = {
    cp_model.OPTIMAL: "OPTIMAL",
    cp_model.FEASIBLE: "FEASIBLE",
    cp_model.INFEASIBLE: "INFEASIBLE",
    cp_model.UNKNOWN: "UNKNOWN"
}

baseline_rules = [
    'restricciones.hard.licencias',
    'restricciones.hard.franco_forzado',
    'restricciones.hard.excluir_turnos',
    'restricciones.hard.fechas_especiales',
    'restricciones.hard.puestos_solo_fijos',
    'restricciones.hard.solo_asignaciones_fijas',
    'restricciones.hard.asignacion_fija_obligatoria',
    'restricciones.hard.cobertura_dinamica',
    'restricciones.hard.un_turno_por_dia',
    'restricciones.hard.mezcla_semanal_dura',
    'restricciones.hard.no_repetir_turno_consecutivo',
    'restricciones.hard.esquema_semanal_enfermeria',
    'restricciones.hard.balance_dia_noche',
    'restricciones.hard.fin_licencia',
    'restricciones.hard.finde_post_licencia',
    'restricciones.hard.franco_previo_lpp',
    'restricciones.hard.turno_previo_licencia',
    'restricciones.hard.patron_ciclico',
    'restricciones.hard.personal_asociado',
    'restricciones.hard.personal_disociado',
    'restricciones.hard.rotacion_mensual_dura',
    'restricciones.hard.max_feriados_anual',
    'restricciones.hard.semanas_seguimiento_requeridas',
    'restricciones.hard.orden_rotacion_semanal',
    'restricciones.hard.exacto_finde_y_dia',
    'restricciones.hard.finds_completos_y_medios',
    'restricciones.hard.exacto_dia_especifico_mes',
    'restricciones.hard.min_findes_mes',
    'restricciones.hard.max_horas_mes_calendario',
    'restricciones.hard.min_horas_mes_calendario',
    'restricciones.hard.max_horas_semana',
    'restricciones.hard.min_horas_semana'
]

remaining_rules = [
    'restricciones.hard.max_dias_continuos',
    'restricciones.hard.max_turnos',
    'restricciones.hard.min_turnos',
    'restricciones.hard.finde_largo_reglamentario',
    'restricciones.hard.brecha_diaria_personal',
    'restricciones.hard.descanso_entre_turnos',
    'restricciones.hard.max_francos_semana',
    'restricciones.hard.max_francos_continuos',
    'restricciones.hard.min_turnos_semana',
    'restricciones.hard.min_francos_semana',
    'restricciones.double.manejo_findes',
    'restricciones.double.no_repetir_n_consecutivo',
    'restricciones.double.repeticion_tipo_semana',
    'restricciones.double.min_francos_consecutivos'
]

def build_model_with_rules(target_rule_name):
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
    
    from restricciones.hard._utils import crear_y_vincular_variables_semanales
    crear_y_vincular_variables_semanales(modelo, ctx)
    
    # 1. Apply DISTANCIA_MINIMA_TIPO_SEMANA
    from restricciones.double import distancia_minima_tipo_semana
    preparar_assumption(modelo, ctx, 'DISTANCIA_MINIMA_TIPO_SEMANA')
    distancia_minima_tipo_semana.apply(modelo, ctx)
    
    # Force it
    for name, var in ctx.assumptions:
        if name == 'REG_DISTANCIA_MINIMA_TIPO_SEMANA':
            modelo.Add(var == 1)
            break
            
    # 2. Apply baseline rules
    for r_name in baseline_rules:
        modulo = importlib.import_module(r_name)
        codigo = r_name.rsplit('.', 1)[-1].upper()
        ctx.codigo_regla = codigo
        preparar_assumption(modelo, ctx, codigo)
        modulo.apply(modelo, ctx)
        ctx.current_assumption = None
        
        # Force it
        for name, var in ctx.assumptions:
            if name == f"REG_{codigo}":
                modelo.Add(var == 1)
                break
                
    # 3. Apply target remaining rule if provided
    if target_rule_name:
        modulo = importlib.import_module(target_rule_name)
        codigo = target_rule_name.rsplit('.', 1)[-1].upper()
        ctx.codigo_regla = codigo
        preparar_assumption(modelo, ctx, codigo)
        modulo.apply(modelo, ctx)
        ctx.current_assumption = None
        
        # Force it
        for name, var in ctx.assumptions:
            if name == f"REG_{codigo}":
                modelo.Add(var == 1)
                break
                
    return modelo

print("=== VERIFICANDO CADA REGLA RESTANTE CONTRA BASELINE ===")
for r_name in remaining_rules:
    codigo = r_name.rsplit('.', 1)[-1].upper()
    modelo_temp = build_model_with_rules(r_name)
    
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 10 # 10 seconds for each check to avoid false UNKNOWN
    status = solver.Solve(modelo_temp)
    status_name = status_names.get(status, "UNKNOWN")
    
    print(f"Baseline + {codigo}: {status_name}")

