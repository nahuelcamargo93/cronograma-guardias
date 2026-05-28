import sys
import os
from datetime import date, timedelta, datetime
from ortools.sat.python import cp_model

sys.path.append(os.path.abspath("."))
import data
from database import queries as db_queries
from database.data_loader import obtener_empleados, obtener_turnos
import rule_engine as _re
import scratch.diagnose_unsat as du

db_queries.init_licencias()
fecha_inicio = "2026-06-01"
fecha_fin = "2026-06-30"
servicio_id = 3

fecha_inicio_dt = datetime.strptime(fecha_inicio, "%Y-%m-%d")
fecha_fin_dt = datetime.strptime(fecha_fin, "%Y-%m-%d")
total_dias = (fecha_fin_dt - fecha_inicio_dt).days + 1
num_semanas = (total_dias + 6) // 7

config_turnos, metadata_turnos_raw, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
    servicio_id=servicio_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
)
reglas_servicio_db = db_queries.cargar_reglas_servicio(servicio_id)
ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)
empleados = obtener_empleados(servicio_id, fecha_inicio, total_dias)
turnos_dict = obtener_turnos(servicio_id)
historial_semana_previa = db_queries.cargar_guardias_previas(fecha_inicio, dias_atras=28, servicio_id=servicio_id)
offset_dia = fecha_inicio_dt.weekday()

feriados_indices = []
from data import FERIADOS
for f_str in FERIADOS:
    f_dt = datetime.strptime(f_str, "%Y-%m-%d")
    delta = (f_dt - fecha_inicio_dt).days
    if 0 <= delta < total_dias:
        feriados_indices.append(delta)

# Baseline scenario:
# We ignore MAX_HORAS_MES_CALENDARIO for all Planta doctors EXCEPT Quintero.
# So we only enforce it for Quintero (and Residentes).
# We want to see which rule is in conflict.
lista_reglas = [
    'ASIGNACION_FIJA', 'LICENCIAS', 'FRANCO_FORZADO', 'MAX_TURNOS', 'EXCLUIR_TURNOS',
    'MIN_TURNOS', 'COBERTURA_DINAMICA', 'LIMITE_HORAS_SEMANALES', 'DESCANSO_ENTRE_TURNOS',
    'MIN_FINDES_MES', 'EXACTO_FINDES_MES', 'UN_SOLO_TURNO_POR_DIA', 'FIN_LICENCIA',
    'MIN_HORAS_MES_CALENDARIO', 'REGLAS_FECHAS_ESPECIALES', 'PATRON_CICLICO',
    'EVITAR_MEZCLA_SEMANAL', 'ROTACION_MENSUAL', 'FINDES_COMPLETOS_Y_MEDIOS',
    'BALANCE_DIA_NOCHE', 'PERSONAL_ASOCIADO', 'MAX_DIAS_CONTINUOS', 'REGLAS_BLANDAS'
]

print("Isolating conflict when Quintero is restricted and others are relaxed:")
for rule_to_ignore in lista_reglas:
    # Build ignore dict: ignore MAX_HORAS_MES_CALENDARIO for all Planta doctors except Quintero
    # AND ignore the current test rule globally.
    ignore_dict = {emp.nombre: ['MAX_HORAS_MES_CALENDARIO'] for emp in empleados if emp.rol != "Residente" and emp.nombre != "Quintero Anabela Belen"}
    
    args_modelo = (empleados, config_turnos, turnos_dict, demanda_req, ajustes_db, total_dias, feriados_indices, offset_dia, num_semanas, reglas_servicio_db, ajustes_reglas, historial_semana_previa, servicio_id)
    
    modelo = du.construir_modelo_test(*args_modelo, reglas_a_ignorar=[rule_to_ignore], reglas_a_ignorar_por_persona=ignore_dict)
    
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 4
    status = solver.Solve(modelo)
    feasible = (status == cp_model.OPTIMAL or status == cp_model.FEASIBLE)
    
    if feasible:
        print(f"  [WARN] If we ignore '{rule_to_ignore}', the model becomes FEASIBLE!")
    else:
        print(f"  - Ignoring '{rule_to_ignore}' does NOT solve the infeasibility.")
