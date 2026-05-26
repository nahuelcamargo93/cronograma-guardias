import sys
import os
sys.path.append(os.path.abspath("."))
from ortools.sat.python import cp_model
from database.data_loader import obtener_empleados, obtener_turnos
from database import queries as db_queries
from data import FECHA_INICIO, FECHA_FIN, FERIADOS, SERVICIO_ID
from datetime import datetime
import rule_engine

fecha_inicio = FECHA_INICIO
fecha_fin = FECHA_FIN
servicio_id = SERVICIO_ID

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
for f_str in FERIADOS:
    f_dt = datetime.strptime(f_str, "%Y-%m-%d")
    delta = (f_dt - fecha_inicio_dt).days
    if 0 <= delta < total_dias:
        feriados_indices.append(delta)

groups = {
    "Group_Bonus": ['BONUS_COMBO_FINDE', 'BONUS_PREFERENCIAS', 'BONUS_SEG_PUNTOS', 'BONUS_SEG_TOTAL', 'TURNOS_PREFERENCIALES'],
    "Group_Brecha": ['PESO_BRECHA_ANUAL', 'PESO_BRECHA_MENSUAL', 'PESO_BRECHA_SEG', 'PESO_BRECHA_MENSUAL_CALENDARIO', 'PESO_BRECHA_DIARIA_PERSONAL'],
    "Group_Equidad": ['PESO_EQUIDAD_FL3', 'PESO_EQUIDAD_FL4', 'PESO_EQUIDAD_FERIADOS', 'PESO_EQUIDAD_FINDES_MENSUAL', 'PESO_EQUIDAD_FINDES_MENSUAL_CALENDARIO', 'PESO_EQUIDAD_FINDES_ANUAL'],
    "Group_Consistencia": ['PESO_INCONSISTENCIA', 'PESO_MIX_HORARIO', 'PENALIZACION_TURNO_AUSENTE', 'PENALIZACION_TURNO']
}

original_resolver = rule_engine.resolver_parametros_regla

def test_groups(deactivated_groups):
    rules_to_deactivate = []
    for g in deactivated_groups:
        rules_to_deactivate.extend(groups[g])
        
    def mocked_resolver(codigo_regla, personal_nombre, fecha, reglas_servicio, reglas_personal, ajustes_personal):
        if codigo_regla in rules_to_deactivate:
            return None
        return original_resolver(codigo_regla, personal_nombre, fecha, reglas_servicio, reglas_personal, ajustes_personal)
        
    rule_engine.resolver_parametros_regla = mocked_resolver
    
    from debug_imposibilidad import construir_modelo_test
    args_modelo = (empleados, config_turnos, turnos_dict, demanda_req, ajustes_db, total_dias, feriados_indices, offset_dia, num_semanas, reglas_servicio_db, ajustes_reglas, historial_semana_previa, servicio_id)
    modelo = construir_modelo_test(*args_modelo)
    
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 2.0
    status = solver.Solve(modelo)
    
    rule_engine.resolver_parametros_regla = original_resolver
    return status == cp_model.OPTIMAL or status == cp_model.FEASIBLE

# Test deactivating one group at a time
print("--- Deactivating ONE group at a time ---")
for g_name in groups:
    if test_groups([g_name]):
        print(f"--> [SUCCESS] Model becomes FEASIBLE when deactivating: {g_name}")
    else:
        print(f"Deactivating {g_name} does not make it feasible.")

# Test deactivating combinations of groups
print("\n--- Deactivating combinations ---")
import itertools
for r in range(2, len(groups)+1):
    for comb in itertools.combinations(groups.keys(), r):
        if test_groups(comb):
            print(f"--> [SUCCESS] Model becomes FEASIBLE when deactivating: {comb}")
            # Exit early on first success to show smallest combo
            sys.exit(0)
