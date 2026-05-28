import sqlite3
import os
import sys
import shutil
from datetime import datetime, date, timedelta
from ortools.sat.python import cp_model

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set temporary DB path
TEMP_DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "temp_solve_print.db")
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

def solve_and_print():
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
    
    # Build model in a way that we can extract the variables
    # Let's import the builder and run it:
    import debug_imposibilidad
    
    # We will subclass CpModel or just inspect its proto variables to find our mappings!
    # A CpModel has variables in its proto. Let's create a map of name -> variable object
    modelo = debug_imposibilidad.construir_modelo_test(
        empleados, config_turnos, turnos_dict, demanda_req, adjustments_db, 
        total_dias, feriados_indices, offset_dia, num_semanas, 
        reglas_servicio_db, ajustes_reglas, historial_semana_previa, SERVICIO_ID
    )
    
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 30
    status = solver.Solve(modelo)
    
    print(f"Solver Status: {solver.StatusName(status)}")
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print("\n=== SOLVED SCHEDULE FOR 18:00 - 23:59 SUPERVISOR ===")
        # Get all Boolean variables from the model by parsing their name
        vars_by_name = {}
        for var_proto in modelo.Proto().variables:
            name = var_proto.name
            if name:
                # We construct a CpSolverVariable using the model and the index
                var_obj = cp_model.BoolVar(modelo, name)
                vars_by_name[name] = var_obj
        
        # Let's print assignments for 18-24_Supervisor (or similar)
        # Shift name is "18-24_Supervisor"
        for dia in range(total_dias):
            fecha_d = fecha_inicio_dt + timedelta(days=dia)
            fecha_str = fecha_d.strftime("%Y-%m-%d")
            
            assigned = []
            for emp in empleados:
                # Find variable like "turno_{emp.nombre}_dia{dia}_18-24_Supervisor"
                var_name = f"turno_{emp.nombre}_dia{dia}_18-24_Supervisor"
                if var_name in vars_by_name:
                    val = solver.Value(vars_by_name[var_name])
                    if val > 0:
                        assigned.append(emp.nombre)
                
                # Let's also check other supervisor shifts to see where people are working
                for t in config_turnos.get("Semana", {}).keys():
                    if "Supervisor" in t:
                        var_name = f"turno_{emp.nombre}_dia{dia}_{t}"
                        if var_name in vars_by_name:
                            val = solver.Value(vars_by_name[var_name])
                            if val > 0 and t != "18-24_Supervisor":
                                print(f"    (Other: {emp.nombre} works {t} on {fecha_str})")
            
            print(f"Day {dia:02d} ({fecha_str}, {fecha_d.strftime('%A')}): Assigned {assigned}")
            
        print("\n=== TOTAL HOURS FOR EACH SUPERVISOR ===")
        for emp in empleados:
            total_horas = 0
            for dia in range(total_dias):
                for t, t_info in turnos_dict.items():
                    var_name = f"turno_{emp.nombre}_dia{dia}_{t}"
                    if var_name in vars_by_name:
                        val = solver.Value(vars_by_name[var_name])
                        if val > 0:
                            total_horas += t_info.horas
            if total_horas > 0:
                print(f"  {emp.nombre} ({emp.categoria}): {total_horas} hours")
    else:
        print("Model is INFEASIBLE.")

if __name__ == "__main__":
    try:
        solve_and_print()
    finally:
        if os.path.exists(TEMP_DB):
            try: os.remove(TEMP_DB)
            except: pass
