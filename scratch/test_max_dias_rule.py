import sqlite3
import os
import sys
import shutil
from datetime import datetime, date, timedelta
from ortools.sat.python import cp_model

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set temporary DB path
TEMP_DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "temp_max_dias.db")
ORIG_DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cronograma_inteligente.db")

if os.path.exists(TEMP_DB):
    try: os.remove(TEMP_DB)
    except: pass
shutil.copyfile(ORIG_DB, TEMP_DB)

import database.connection
database.connection.DB_PATH = TEMP_DB

from debug_imposibilidad import construir_modelo_test
from database import queries as db_queries
from database.data_loader import obtener_empleados, obtener_turnos
from data import SERVICIO_ID, FECHA_INICIO, FECHA_FIN, FERIADOS

def apply_test_configuration(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. First, make sure the basic database fixes for Servicio 4 are applied (including Noelia and Irma)
    new_exclusions_noelia = '{"turnos": ["06-12_Monitorista", "12-18_Monitorista", "18-24_Monitorista", "06-12_Supervisor", "12-18_Supervisor", "18-24_Supervisor"]}'
    cursor.execute("""
        UPDATE personal_reglas
        SET parametros_json = ?
        WHERE personal_nombre = 'GUERRIDO Noelia' AND codigo_regla = 'EXCLUIR_TURNOS'
    """, (new_exclusions_noelia,))
    
    # Add Noelia's hours adjustments (114 hours)
    cursor.execute("SELECT 1 FROM personal_reglas_ajustes WHERE personal_nombre = 'GUERRIDO Noelia' AND codigo_regla = 'MIN_HORAS_MES_CALENDARIO'")
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo)
            VALUES 
            ('GUERRIDO Noelia', 'MIN_HORAS_MES_CALENDARIO', '2026-06-01', '2026-06-30', 'SOBRESCRIBIR', '{"min_horas": 114}', 1),
            ('GUERRIDO Noelia', 'MAX_HORAS_MES_CALENDARIO', '2026-06-01', '2026-06-30', 'SOBRESCRIBIR', '{"max_horas": 114}', 1)
        """)
    
    # Update Brizuela Irma to cover Category D shifts
    new_exclusions_irma = '{"turnos": ["00-06_Monitorista", "12-18_Monitorista", "18-24_Monitorista", "00-06_Supervisor", "06-12_Supervisor"]}'
    cursor.execute("""
        UPDATE personal_reglas
        SET parametros_json = ?
        WHERE personal_nombre = 'BRIZUELA Irma' AND codigo_regla = 'EXCLUIR_TURNOS'
    """, (new_exclusions_irma,))
    
    # 2. Configure MAX_DIAS_CONTINUOS rule for SUAREZ Carolina: max 6 days
    cursor.execute("""
        INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo)
        VALUES 
        ('SUAREZ Carolina', 'MAX_DIAS_CONTINUOS', '2026-06-01', '2026-06-30', 'SOBRESCRIBIR', '{"max_dias": 6}', 1)
    """)
    
    conn.commit()
    conn.close()

def run_test():
    apply_test_configuration(TEMP_DB)
    
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
    
    # Let's mock a previous cycle history for SUAREZ Carolina:
    # Worked 6 consecutive days at the end of May (May 26, 27, 28, 29, 30, 31)
    historial_semana_previa = {
        'SUAREZ Carolina': [
            {'fecha': '2026-05-26', 'turno': '18-24_Supervisor'},
            {'fecha': '2026-05-27', 'turno': '18-24_Supervisor'},
            {'fecha': '2026-05-28', 'turno': '18-24_Supervisor'},
            {'fecha': '2026-05-29', 'turno': '18-24_Supervisor'},
            {'fecha': '2026-05-30', 'turno': '18-24_Supervisor'},
            {'fecha': '2026-05-31', 'turno': '18-24_Supervisor'}
        ]
    }
    
    offset_dia = fecha_inicio_dt.weekday()
    
    args_modelo = (empleados, config_turnos, turnos_dict, demanda_req, adjustments_db, total_dias, feriados_indices, offset_dia, num_semanas, reglas_servicio_db, ajustes_reglas, historial_semana_previa, SERVICIO_ID)
    
    modelo = construir_modelo_test(*args_modelo)
    
    # We want to extract the assignment variables for SUAREZ Carolina for day 0 (June 1st)
    vars_by_name = {}
    for idx, var_proto in enumerate(modelo.Proto().variables):
        name = var_proto.name
        if name:
            vars_by_name[name] = modelo.GetIntVarFromProtoIndex(idx)
            
    # Run solver
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 30
    status = solver.Solve(modelo)
    
    print(f"Solver Status: {solver.StatusName(status)}")
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        # Check if Carolina worked on June 1st (day 0)
        # Shift name for Carolina: "18-24_Supervisor"
        var_name = f"turno_SUAREZ Carolina_dia0_18-24_Supervisor"
        carolina_worked_day0 = 0
        if var_name in vars_by_name:
            carolina_worked_day0 = solver.Value(vars_by_name[var_name])
            
        print(f"SUAREZ Carolina assignment on June 1st (dia 0): {carolina_worked_day0}")
        if carolina_worked_day0 == 0:
            print("[TEST PASSED] Carolina Suarez was correctly FORCED TO REST on June 1st to satisfy the MAX_DIAS_CONTINUOS rule!")
        else:
            print("[TEST FAILED] Carolina Suarez worked on June 1st, violating the MAX_DIAS_CONTINUOS rule.")
    else:
        print("[TEST ERROR] The model became INFEASIBLE.")

if __name__ == "__main__":
    try:
        run_test()
    finally:
        if os.path.exists(TEMP_DB):
            try: os.remove(TEMP_DB)
            except: pass
