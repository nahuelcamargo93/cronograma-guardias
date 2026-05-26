import sys
sys.path.insert(0, '')
import sqlite3
import json
import datetime
from datetime import date, timedelta
import pandas as pd
from data import FECHA_INICIO, FECHA_FIN, FERIADOS
from database.data_loader import obtener_empleados, obtener_turnos
import database.queries as db_queries
import main as wfm_main
import rule_engine as _re

def count_available_weekends(emp, fecha_inicio_dt, dias_del_bloque, feriados_indices, offset_dia):
    findes = {}
    for d in range(dias_del_bloque):
        fecha_d = fecha_inicio_dt + timedelta(days=d)
        dia_semana = (d + offset_dia) % 7
        es_finde = (dia_semana >= 5) or (d in feriados_indices)
        if es_finde:
            lunes = (fecha_d - timedelta(days=fecha_d.weekday())).isoformat()
            findes.setdefault(lunes, []).append(d)
    
    k = sum(1 for lunes, dias in findes.items() if any(d not in emp.dias_licencia for d in dias))
    return k, findes

def get_expected_targets(k):
    # Weekends:
    if k >= 2:
        expected_weekends = 2
    elif k == 1:
        expected_weekends = 1
    else:
        expected_weekends = 0
        
    # Fridays:
    if k >= 4:
        expected_fridays = 1
    elif k == 3:
        expected_fridays = 0
    elif k == 2:
        expected_fridays = 1
    else:
        expected_fridays = 0
        
    return expected_weekends, expected_fridays

def get_actual_counts(df_res, emp_nombre, fecha_inicio_dt, findes, feriados_indices):
    emp_df = df_res[df_res['Personal'] == emp_nombre] if df_res is not None else pd.DataFrame()
    worked_days = set()
    for _, row in emp_df.iterrows():
        f_dt = date.fromisoformat(row['Fecha'])
        delta = (f_dt - fecha_inicio_dt).days
        worked_days.add(delta)
        
    # Count weekends worked
    worked_findes = 0
    for lunes, dias in findes.items():
        if any(d in worked_days for d in dias):
            worked_findes += 1
            
    # Count Fridays worked
    worked_fridays = 0
    for d in worked_days:
        f_dt = fecha_inicio_dt + timedelta(days=d)
        if f_dt.weekday() == 4: # Friday is 4
            worked_fridays += 1
            
    return worked_findes, worked_fridays

def run_test(case_name, exact_mode=False):
    print(f"\n==================================================")
    print(f"RUNNING TEST CASE: {case_name}")
    print(f"==================================================")
    
    # Configure DB rules
    conn = sqlite3.connect('cronograma_inteligente.db')
    cur = conn.cursor()
    
    # Get the rule IDs
    cur.execute("SELECT id FROM reglas_catalogo WHERE codigo_regla = 'MIN_FINDES_MES'")
    min_findes_id = cur.fetchone()[0]
    cur.execute("SELECT id FROM reglas_catalogo WHERE codigo_regla = 'MIN_DIA_ESPECIFICO_MES'")
    min_dia_id = cur.fetchone()[0]
    
    cur.execute("SELECT id FROM reglas_catalogo WHERE codigo_regla = 'EXACTO_FINDES_MES'")
    exacto_findes_id = cur.fetchone()[0]
    cur.execute("SELECT id FROM reglas_catalogo WHERE codigo_regla = 'EXACTO_DIA_ESPECIFICO_MES'")
    exacto_dia_id = cur.fetchone()[0]
    
    # Reset/Update rules based on exact_mode
    if exact_mode:
        # Suspend MIN rules
        cur.execute("UPDATE servicios_reglas SET parametros_json = ? WHERE servicio_id = 3 AND regla_id = ?",
                    (json.dumps({"min_findes": 2, "dinamico_licencias": True, "suspendida": True}), min_findes_id))
        cur.execute("UPDATE servicios_reglas SET parametros_json = ? WHERE servicio_id = 3 AND regla_id = ?",
                    (json.dumps({"dia_semana": "Viernes", "min_dias": 1, "dinamico_licencias": True, "suspendida": True}), min_dia_id))
        
        # Activate EXACT rules
        cur.execute("UPDATE servicios_reglas SET parametros_json = ? WHERE servicio_id = 3 AND regla_id = ?",
                    (json.dumps({"exacto_findes": 2, "dinamico_licencias": True, "suspendida": False}), exacto_findes_id))
        cur.execute("UPDATE servicios_reglas SET parametros_json = ? WHERE servicio_id = 3 AND regla_id = ?",
                    (json.dumps({"dia_semana": "Viernes", "exacto_dias": 1, "dinamico_licencias": True, "suspendida": False}), exacto_dia_id))
        
        # Suspend MAX_TURNOS, MAX_HORAS_MES_CALENDARIO, MIN_HORAS_MES_CALENDARIO, ASIGNACION_FIJA for all service 3 employees to make Case B mathematically feasible
        cur.execute("SELECT nombre FROM personal WHERE servicio_id = 3")
        service3_employees = [r[0] for r in cur.fetchall()]
        rules_to_suspend = ['MAX_TURNOS', 'MAX_HORAS_MES_CALENDARIO', 'MIN_HORAS_MES_CALENDARIO', 'ASIGNACION_FIJA']
        for emp_name in service3_employees:
            for rule in rules_to_suspend:
                # Check if suspension already exists
                cur.execute("""
                    SELECT COUNT(*) FROM personal_reglas_ajustes
                    WHERE personal_nombre = ? AND codigo_regla = ? AND accion = 'SUSPENDER'
                    AND fecha_inicio = ? AND fecha_fin = ?
                """, (emp_name, rule, FECHA_INICIO, FECHA_FIN))
                if cur.fetchone()[0] == 0:
                    cur.execute("""
                        INSERT INTO personal_reglas_ajustes 
                        (personal_nombre, codigo_regla, accion, parametros_json, fecha_inicio, fecha_fin)
                        VALUES (?, ?, 'SUSPENDER', '{}', ?, ?)
                    """, (emp_name, rule, FECHA_INICIO, FECHA_FIN))
    else:
        # Activate MIN rules
        cur.execute("UPDATE servicios_reglas SET parametros_json = ? WHERE servicio_id = 3 AND regla_id = ?",
                    (json.dumps({"min_findes": 2, "dinamico_licencias": True, "suspendida": False}), min_findes_id))
        cur.execute("UPDATE servicios_reglas SET parametros_json = ? WHERE servicio_id = 3 AND regla_id = ?",
                    (json.dumps({"dia_semana": "Viernes", "min_dias": 1, "dinamico_licencias": True, "suspendida": False}), min_dia_id))
        
        # Suspend EXACT rules
        cur.execute("UPDATE servicios_reglas SET parametros_json = ? WHERE servicio_id = 3 AND regla_id = ?",
                    (json.dumps({"exacto_findes": 2, "dinamico_licencias": True, "suspendida": True}), exacto_findes_id))
        cur.execute("UPDATE servicios_reglas SET parametros_json = ? WHERE servicio_id = 3 AND regla_id = ?",
                    (json.dumps({"dia_semana": "Viernes", "exacto_dias": 1, "dinamico_licencias": True, "suspendida": True}), exacto_dia_id))
        
        # Remove any temporary suspensions we added
        rules_to_suspend = ['MAX_TURNOS', 'MAX_HORAS_MES_CALENDARIO', 'MIN_HORAS_MES_CALENDARIO', 'ASIGNACION_FIJA']
        for rule in rules_to_suspend:
            cur.execute("""
                DELETE FROM personal_reglas_ajustes 
                WHERE codigo_regla = ? AND accion = 'SUSPENDER' AND parametros_json = '{}'
                AND fecha_inicio = ? AND fecha_fin = ?
            """, (rule, FECHA_INICIO, FECHA_FIN))
        
    conn.commit()
    conn.close()
    
    # Run solver
    fecha_inicio_dt = datetime.datetime.strptime(FECHA_INICIO, "%Y-%m-%d")
    fecha_fin_dt = datetime.datetime.strptime(FECHA_FIN, "%Y-%m-%d")
    DIAS_DEL_BLOQUE = (fecha_fin_dt - fecha_inicio_dt).days + 1
    num_semanas = (DIAS_DEL_BLOQUE + 6) // 7
    offset_dia = fecha_inicio_dt.weekday()
    
    feriados_indices = []
    for f_str in FERIADOS:
        f_dt = datetime.datetime.strptime(f_str, "%Y-%m-%d")
        delta = (f_dt - fecha_inicio_dt).days
        if 0 <= delta < DIAS_DEL_BLOQUE:
            feriados_indices.append(delta)
            
    empleados = obtener_empleados(3, FECHA_INICIO, DIAS_DEL_BLOQUE)
    config_turnos, metadata_turnos_raw, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
        servicio_id=3, fecha_inicio=FECHA_INICIO, fecha_fin=FECHA_FIN
    )
    reglas_servicio_db = db_queries.cargar_reglas_servicio(3)
    ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(FECHA_INICIO, FECHA_FIN)
    turnos_dict = obtener_turnos(3)
    historial_semana_previa = db_queries.cargar_guardias_previas(FECHA_INICIO, dias_atras=28, servicio_id=3)
    
    print("\nStarting optimization...")
    modelo, turnos, flr_tracker, vars_turno_sem = wfm_main.construir_modelo(
        empleados, config_turnos, turnos_dict, demanda_req, ajustes_db,
        DIAS_DEL_BLOQUE, feriados_indices, offset_dia, num_semanas,
        reglas_servicio=reglas_servicio_db,
        ajustes_reglas_personal=ajustes_reglas,
        historial_semana_previa=historial_semana_previa,
        servicio_id=3
    )
    
    # Solve with a smaller timeout (30 seconds) for faster testing
    df_res, flrs, df_cat = wfm_main.resolver_modelo(
        modelo, turnos, flr_tracker, empleados, DIAS_DEL_BLOQUE, feriados_indices, 
        FECHA_INICIO, offset_dia, config_turnos, vars_turno_sem=vars_turno_sem,
        max_time_in_seconds=30
    )
    
    if df_res is None:
        print(f"FAILED: Solver returned INFEASIBLE or TIMEOUT for Case {case_name}")
        return False
        
    print("\nComparing targets and actual assignments...")
    all_ok = True
    for emp in empleados:
        k, findes = count_available_weekends(emp, date.fromisoformat(FECHA_INICIO), DIAS_DEL_BLOQUE, feriados_indices, offset_dia)
        
        # Resolve rule parameters to check if rules are active/suspended
        params_w = _re.resolver_parametros_regla(
            'EXACTO_FINDES_MES' if exact_mode else 'MIN_FINDES_MES',
            emp.nombre, FECHA_INICIO, reglas_servicio_db, emp.reglas, ajustes_reglas
        )
        params_f = _re.resolver_parametros_regla(
            'EXACTO_DIA_ESPECIFICO_MES' if exact_mode else 'MIN_DIA_ESPECIFICO_MES',
            emp.nombre, FECHA_INICIO, reglas_servicio_db, emp.reglas, ajustes_reglas
        )
        
        has_w = _re.regla_existe(params_w) and not _re.regla_suspendida(params_w)
        has_f = _re.regla_existe(params_f) and not _re.regla_suspendida(params_f)
        
        # If the minimum rule is suspended for this employee, inherited by EXACT
        if exact_mode and params_w is not None:
            # Check if MIN_FINDES_MES was suspended for this employee
            params_min_w = _re.resolver_parametros_regla(
                'MIN_FINDES_MES', emp.nombre, FECHA_INICIO, reglas_servicio_db, emp.reglas, ajustes_reglas
            )
            if _re.regla_suspendida(params_min_w):
                has_w = False
                
        if exact_mode and params_f is not None:
            # Check if MIN_DIA_ESPECIFICO_MES was suspended for this employee
            params_min_f = _re.resolver_parametros_regla(
                'MIN_DIA_ESPECIFICO_MES', emp.nombre, FECHA_INICIO, reglas_servicio_db, emp.reglas, ajustes_reglas
            )
            if _re.regla_suspendida(params_min_f):
                has_f = False
                
        exp_w, exp_f = get_expected_targets(k)
        if not has_w:
            exp_w = 0
        if not has_f:
            exp_f = 0
            
        act_w, act_f = get_actual_counts(df_res, emp.nombre, date.fromisoformat(FECHA_INICIO), findes, feriados_indices)
        
        # Check assertions
        if exact_mode:
            w_ok = (act_w == exp_w)
            f_ok = (act_f == exp_f)
            check_str_w = "=="
            check_str_f = "=="
        else:
            w_ok = (act_w >= exp_w)
            f_ok = (act_f >= exp_f)
            check_str_w = ">="
            check_str_f = ">="
            
        status_w = "OK" if w_ok else ("SKIP" if not has_w else "FAIL")
        status_f = "OK" if f_ok else ("SKIP" if not has_f else "FAIL")
        
        print(f"Professional: {emp.nombre:<30} | k={k} | "
              f"Weekends: actual={act_w} {check_str_w} expected={exp_w} ({status_w}) | "
              f"Fridays: actual={act_f} {check_str_f} expected={exp_f} ({status_f})")
              
        if (has_w and not w_ok) or (has_f and not f_ok):
            all_ok = False
            
    if all_ok:
        print(f"\n[SUCCESS] Case {case_name} verified successfully!")
    else:
        print(f"\n[FAILURE] Case {case_name} had validation failures.")
        
    return all_ok

def main():
    try:
        # Case A: Minimum rules
        ok_min = run_test("Case A: Minimum Rules (dinamico_licencias=True)", exact_mode=False)
        
        # Case B: Exact rules
        ok_exact = run_test("Case B: Exact Rules (dinamico_licencias=True)", exact_mode=True)
        
        if ok_min and ok_exact:
            print("\n*** ALL TESTS PASSED SUCCESSFULLY! ***")
        else:
            print("\n*** SOME TESTS FAILED! ***")
    finally:
        # Restore defaults: MIN active, EXACT suspended
        conn = sqlite3.connect('cronograma_inteligente.db')
        cur = conn.cursor()
        cur.execute("SELECT id FROM reglas_catalogo WHERE codigo_regla = 'MIN_FINDES_MES'")
        min_findes_id = cur.fetchone()[0]
        cur.execute("SELECT id FROM reglas_catalogo WHERE codigo_regla = 'MIN_DIA_ESPECIFICO_MES'")
        min_dia_id = cur.fetchone()[0]
        cur.execute("SELECT id FROM reglas_catalogo WHERE codigo_regla = 'EXACTO_FINDES_MES'")
        exacto_findes_id = cur.fetchone()[0]
        cur.execute("SELECT id FROM reglas_catalogo WHERE codigo_regla = 'EXACTO_DIA_ESPECIFICO_MES'")
        exacto_dia_id = cur.fetchone()[0]
        
        cur.execute("UPDATE servicios_reglas SET parametros_json = ? WHERE servicio_id = 3 AND regla_id = ?",
                    (json.dumps({"min_findes": 2, "dinamico_licencias": True, "suspendida": False}), min_findes_id))
        cur.execute("UPDATE servicios_reglas SET parametros_json = ? WHERE servicio_id = 3 AND regla_id = ?",
                    (json.dumps({"dia_semana": "Viernes", "min_dias": 1, "dinamico_licencias": True, "suspendida": False}), min_dia_id))
        cur.execute("UPDATE servicios_reglas SET parametros_json = ? WHERE servicio_id = 3 AND regla_id = ?",
                    (json.dumps({"exacto_findes": 2, "dinamico_licencias": True, "suspendida": True}), exacto_findes_id))
        cur.execute("UPDATE servicios_reglas SET parametros_json = ? WHERE servicio_id = 3 AND regla_id = ?",
                    (json.dumps({"dia_semana": "Viernes", "exacto_dias": 1, "dinamico_licencias": True, "suspendida": True}), exacto_dia_id))
        
        # Clean up temporary adjustments in case any remain
        rules_to_suspend = ['MAX_TURNOS', 'MAX_HORAS_MES_CALENDARIO', 'MIN_HORAS_MES_CALENDARIO', 'ASIGNACION_FIJA']
        for rule in rules_to_suspend:
            cur.execute("""
                DELETE FROM personal_reglas_ajustes 
                WHERE codigo_regla = ? AND accion = 'SUSPENDER' AND parametros_json = '{}'
                AND fecha_inicio = ? AND fecha_fin = ?
            """, (rule, FECHA_INICIO, FECHA_FIN))
        
        conn.commit()
        conn.close()
        print("\nOriginal database rules configuration restored.")

if __name__ == "__main__":
    main()
