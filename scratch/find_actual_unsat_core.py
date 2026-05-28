import sqlite3
import os
import sys
import shutil
import inspect
from datetime import datetime, date, timedelta
from ortools.sat.python import cp_model

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set temporary DB path
TEMP_DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "temp_unsat_core_actual.db")
ORIG_DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cronograma_inteligente.db")

if os.path.exists(TEMP_DB):
    try: os.remove(TEMP_DB)
    except: pass
shutil.copyfile(ORIG_DB, TEMP_DB)

import database.connection
database.connection.DB_PATH = TEMP_DB

# Dict to store assumption literals
rule_assumptions = {}
assumptions_desc = {}  # index -> description
assumptions_list = []

original_add = cp_model.CpModel.add
original_add_implication = cp_model.CpModel.add_implication
original_add_max_equality = cp_model.CpModel.add_max_equality
original_add_min_equality = cp_model.CpModel.add_min_equality

def get_assumption_for_rule(model, rule_name):
    if rule_name not in rule_assumptions:
        lit = model.NewBoolVar(rule_name)
        rule_assumptions[rule_name] = lit
        assumptions_desc[lit.Index()] = rule_name
        assumptions_list.append(lit)
    return rule_assumptions[rule_name]

def find_rule_caller():
    for frame_info in inspect.stack():
        name = frame_info.function
        if name.startswith('_aplicar_'):
            return name
    return None

def my_add(self, constraint):
    c = original_add(self, constraint)
    caller = find_rule_caller()
    if caller:
        lit = get_assumption_for_rule(self, caller)
        c.OnlyEnforceIf(lit)
    return c

def my_add_implication(self, a, b):
    c = original_add_implication(self, a, b)
    caller = find_rule_caller()
    if caller:
        lit = get_assumption_for_rule(self, caller)
        c.OnlyEnforceIf(lit)
    return c

def my_add_max_equality(self, target, variables):
    c = original_add_max_equality(self, target, variables)
    caller = find_rule_caller()
    if caller:
        lit = get_assumption_for_rule(self, caller)
        c.OnlyEnforceIf(lit)
    return c

def my_add_min_equality(self, target, variables):
    c = original_add_min_equality(self, target, variables)
    caller = find_rule_caller()
    if caller:
        lit = get_assumption_for_rule(self, caller)
        c.OnlyEnforceIf(lit)
    return c

# Apply monkeypatch
cp_model.CpModel.add = my_add
cp_model.CpModel.add_implication = my_add_implication
cp_model.CpModel.add_max_equality = my_add_max_equality
cp_model.CpModel.add_min_equality = my_add_min_equality

from debug_imposibilidad import construir_modelo_test
from database import queries as db_queries
from database.data_loader import obtener_empleados, obtener_turnos
from data import SERVICIO_ID, FECHA_INICIO, FECHA_FIN, FERIADOS

def apply_fixes(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Update EXCLUIR_TURNOS for GUERRIDO Noelia to Category A exclusions
    new_exclusions = '{"turnos": ["06-12_Monitorista", "12-18_Monitorista", "18-24_Monitorista", "06-12_Supervisor", "12-18_Supervisor", "18-24_Supervisor"]}'
    cursor.execute("""
        UPDATE personal_reglas
        SET parametros_json = ?
        WHERE personal_nombre = 'GUERRIDO Noelia' AND codigo_regla = 'EXCLUIR_TURNOS'
    """, (new_exclusions,))
    
    # 2. Add hour adjustments (114 hours) to GUERRIDO Noelia
    cursor.execute("""
        INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo)
        VALUES 
        ('GUERRIDO Noelia', 'MIN_HORAS_MES_CALENDARIO', '2026-06-01', '2026-06-30', 'SOBRESCRIBIR', '{"min_horas": 114}', 1),
        ('GUERRIDO Noelia', 'MAX_HORAS_MES_CALENDARIO', '2026-06-01', '2026-06-30', 'SOBRESCRIBIR', '{"max_horas": 114}', 1)
    """)
    
    # 3. Suspend FINDES_COMPLETOS_Y_MEDIOS for SUAREZ Carolina
    cursor.execute("""
        UPDATE personal_reglas_ajustes
        SET accion = 'SUSPENDER'
        WHERE personal_nombre = 'SUAREZ Carolina' AND codigo_regla = 'FINDES_COMPLETOS_Y_MEDIOS'
    """)
    
    conn.commit()
    conn.close()

def main():
    apply_fixes(TEMP_DB)
    
    db_queries.init_licencias()
    fecha_inicio_dt = datetime.strptime(FECHA_INICIO, "%Y-%m-%d")
    fecha_fin_dt    = datetime.strptime(FECHA_FIN,    "%Y-%m-%d")
    total_dias = (fecha_fin_dt - fecha_inicio_dt).days + 1
    num_semanas = (total_dias + 6) // 7
    
    feriados_indices = []
    for f_str in FERIADOS:
        f_dt = datetime.strptime(f_str, "%Y-%m-%d")
        delta = (f_dt - fecha_inicio_dt).days
        if 0 <= delta < total_dias:
            feriados_indices.append(delta)
            
    config_turnos, metadata_turnos_raw, demanda_req, adjustments_db = db_queries.cargar_configuracion_turnos(
        servicio_id=SERVICIO_ID, fecha_inicio=FECHA_INICIO, fecha_fin=FECHA_FIN
    )
    reglas_servicio_db = db_queries.cargar_reglas_servicio(SERVICIO_ID)
    ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(FECHA_INICIO, FECHA_FIN)
    empleados = obtener_empleados(SERVICIO_ID, FECHA_INICIO, total_dias)
    turnos_dict = obtener_turnos(SERVICIO_ID)
    historial_semana_previa = db_queries.cargar_guardias_previas(FECHA_INICIO, dias_atras=28, servicio_id=SERVICIO_ID)
    offset_dia = fecha_inicio_dt.weekday()
    
    args_modelo = (empleados, config_turnos, turnos_dict, demanda_req, adjustments_db, total_dias, feriados_indices, offset_dia, num_semanas, reglas_servicio_db, ajustes_reglas, historial_semana_previa, SERVICIO_ID)
    
    modelo = construir_modelo_test(*args_modelo)
    
    # Solve with assumptions
    modelo.AddAssumptions(assumptions_list)
    
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 30
    status = solver.Solve(modelo)
    
    print(f"Solver Status: {solver.StatusName(status)}")
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print("SUCCESS: Feasible when all rules are active? That shouldn't happen unless fixes resolved it.")
    elif status == cp_model.INFEASIBLE:
        print("\n=== ISOLATED UNSAT CORE RULES ===")
        core = solver.SufficientAssumptionsForInfeasibility()
        for idx in core:
            print(f"  Conflict: {assumptions_desc[idx]}")
    else:
        print("Solver could not decide in time.")

if __name__ == "__main__":
    try:
        main()
    finally:
        if os.path.exists(TEMP_DB):
            try: os.remove(TEMP_DB)
            except: pass
