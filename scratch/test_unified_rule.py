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
from ortools.sat.python import cp_model

def count_available_weekends_and_fridays(emp, fecha_inicio_dt, dias_del_bloque, feriados_indices, offset_dia, dia_semana_target=4):
    findes = {}
    for d in range(dias_del_bloque):
        fecha_d = fecha_inicio_dt + timedelta(days=d)
        dia_semana = (d + offset_dia) % 7
        es_finde = (dia_semana >= 5) or (d in feriados_indices)
        if es_finde:
            lunes = (fecha_d - timedelta(days=fecha_d.weekday())).isoformat()
            findes.setdefault(lunes, []).append(d)
    
    k = sum(1 for lunes, dias in findes.items() if any(d not in emp.dias_licencia for d in dias))
    
    k_dia = 0
    for d in range(dias_del_bloque):
        fecha_d = fecha_inicio_dt + timedelta(days=d)
        if fecha_d.weekday() == dia_semana_target:
            if d not in emp.dias_licencia:
                k_dia += 1
                
    return k, k_dia, findes

def get_expected_targets(k, k_dia):
    # Mapping findes: 5->2, 4->2, 3->2, 2->1, 1->1, 0->0
    if k >= 3:
        expected_weekends = 2
    elif k >= 1:
        expected_weekends = 1
    else:
        expected_weekends = 0
        
    # Mapping fridays: 5->2, 4->1, 3->0, 2->1, 1->0, 0->0
    if k_dia == 5:
        expected_fridays = 2
    elif k_dia in (4, 2):
        expected_fridays = 1
    else:
        expected_fridays = 0
        
    return expected_weekends, expected_fridays

def get_actual_counts(df_res, emp_nombre, fecha_inicio_dt, findes, dia_semana_target=4):
    emp_df = df_res[df_res['Personal'] == emp_nombre] if df_res is not None else pd.DataFrame()
    worked_days = set()
    for _, row in emp_df.iterrows():
        f_dt = date.fromisoformat(row['Fecha'])
        delta = (f_dt - fecha_inicio_dt).days
        worked_days.add(delta)
        
    worked_findes = 0
    for lunes, dias in findes.items():
        if any(d in worked_days for d in dias):
            worked_findes += 1
            
    worked_fridays = 0
    for d in worked_days:
        f_dt = fecha_inicio_dt + timedelta(days=d)
        if f_dt.weekday() == dia_semana_target:
            worked_fridays += 1
            
    return worked_findes, worked_fridays

def run_test(case_name, mode="HARD"):
    print(f"\n==================================================")
    print(f"RUNNING TEST CASE: {case_name} (Mode={mode})")
    print(f"==================================================")
    
    conn = sqlite3.connect('cronograma_inteligente.db')
    cur = conn.cursor()
    
    # 1. Register/Ensure rule in catalog
    cur.execute("SELECT id FROM reglas_catalogo WHERE codigo_regla = 'EXACTO_FINDE_Y_DIA'")
    row = cur.fetchone()
    if not row:
        cur.execute("""
            INSERT INTO reglas_catalogo (codigo_regla, tipo, descripcion)
            VALUES ('EXACTO_FINDE_Y_DIA', 'HARD', 'Unified rule')
        """)
        conn.commit()
        cur.execute("SELECT id FROM reglas_catalogo WHERE codigo_regla = 'EXACTO_FINDE_Y_DIA'")
        row = cur.fetchone()
        
    rule_id = row[0]
    
    # 2. Setup JSON config
    params_json = {
        "dia_semana": "Viernes",
        "findes_por_disponibilidad": {"5": 2, "4": 2, "3": 2, "2": 1, "1": 1, "0": 0},
        "dias_por_disponibilidad": {"5": 2, "4": 1, "3": 0, "2": 1, "1": 0, "0": 0},
        "modo": mode,
        "peso_soft": 100000
    }
    
    # Enable rule for service 3 and suspend other conflicting rules to ensure feasibility
    cur.execute("""
        INSERT OR REPLACE INTO servicios_reglas (servicio_id, codigo_regla, parametros_json, activo)
        VALUES (3, 'EXACTO_FINDE_Y_DIA', ?, 1)
    """, (json.dumps(params_json),))
    
    # Suspend older Friday/Weekend rules
    for r in ['MIN_FINDES_MES', 'EXACTO_FINDES_MES', 'MIN_DIA_ESPECIFICO_MES', 'EXACTO_DIA_ESPECIFICO_MES']:
        cur.execute("UPDATE servicios_reglas SET activo = 0 WHERE servicio_id = 3 AND codigo_regla = ?", (r,))
        
    # Temporary suspend helper rules for service 3 to avoid conflicting limits in tests
    cur.execute("SELECT nombre FROM personal WHERE servicio_id = 3")
    service3_employees = [r[0] for r in cur.fetchall()]
    rules_to_suspend = ['MAX_TURNOS', 'MAX_HORAS_MES_CALENDARIO', 'MIN_HORAS_MES_CALENDARIO', 'ASIGNACION_FIJA']
    for emp_name in service3_employees:
        for rule in rules_to_suspend:
            cur.execute("""
                INSERT OR IGNORE INTO personal_reglas_ajustes 
                (personal_nombre, codigo_regla, accion, parametros_json, fecha_inicio, fecha_fin)
                VALUES (?, ?, 'SUSPENDER', '{}', ?, ?)
            """, (emp_name, rule, FECHA_INICIO, FECHA_FIN))
            
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
    config_turnos, _, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(3, FECHA_INICIO, FECHA_FIN)
    reglas_servicio_db = db_queries.cargar_reglas_servicio(3)
    ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(FECHA_INICIO, FECHA_FIN)
    turnos_dict = obtener_turnos(3)
    historial_semana_previa = db_queries.cargar_guardias_previas(FECHA_INICIO, dias_atras=28, servicio_id=3)
    
    modelo, turnos_vars, flr_tracker, vars_turno_sem = wfm_main.construir_modelo(
        empleados, config_turnos, turnos_dict, demanda_req, ajustes_db,
        DIAS_DEL_BLOQUE, feriados_indices, offset_dia, num_semanas,
        reglas_servicio=reglas_servicio_db,
        ajustes_reglas_personal=ajustes_reglas,
        historial_semana_previa=historial_semana_previa,
        servicio_id=3
    )
    
    df_res, _, _ = wfm_main.resolver_modelo(
        modelo, turnos_vars, flr_tracker, empleados, DIAS_DEL_BLOQUE, feriados_indices, 
        FECHA_INICIO, offset_dia, config_turnos, vars_turno_sem=vars_turno_sem,
        max_time_in_seconds=20
    )
    
    if df_res is None:
        print(f"FAILED: Solver returned INFEASIBLE or TIMEOUT")
        return False
        
    print("\nComparing targets and actual assignments:")
    all_ok = True
    for emp in empleados:
        k, k_dia, findes = count_available_weekends_and_fridays(emp, date.fromisoformat(FECHA_INICIO), DIAS_DEL_BLOQUE, feriados_indices, offset_dia)
        
        # Verify using resolved parameters
        p_unified = _re.resolver_parametros_regla('EXACTO_FINDE_Y_DIA', emp.nombre, FECHA_INICIO, reglas_servicio_db, emp.reglas, ajustes_reglas)
        has_unified = _re.regla_existe(p_unified) and not _re.regla_suspendida(p_unified)
        
        exp_w, exp_f = get_expected_targets(k, k_dia)
        if not has_unified:
            exp_w, exp_f = 0, 0
            
        act_w, act_f = get_actual_counts(df_res, emp.nombre, date.fromisoformat(FECHA_INICIO), findes)
        
        w_ok = (act_w == exp_w)
        f_ok = (act_f == exp_f)
        
        status_w = "OK" if w_ok else ("SKIP" if not has_unified else "FAIL")
        status_f = "OK" if f_ok else ("SKIP" if not has_unified else "FAIL")
        
        print(f"  Professional: {emp.nombre:<25} | k={k}, k_dia={k_dia} | "
              f"Weekends: actual={act_w} expected={exp_w} ({status_w}) | "
              f"Fridays: actual={act_f} expected={exp_f} ({status_f})")
              
        if has_unified:
            if mode == "HARD" and (not w_ok or not f_ok):
                all_ok = False
            elif mode == "SOFT" and (not w_ok or not f_ok):
                # In soft mode, a difference is allowed but should be penalized.
                # So we just print warning, it doesn't fail the logic test.
                pass
            
    return all_ok

def restore_rules():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cur = conn.cursor()
    
    # Disable EXACTO_FINDE_Y_DIA for service 3
    cur.execute("DELETE FROM servicios_reglas WHERE servicio_id = 3 AND codigo_regla = 'EXACTO_FINDE_Y_DIA'")
    
    # Restore older rules for service 3
    for r in ['MIN_FINDES_MES', 'MIN_DIA_ESPECIFICO_MES']:
        cur.execute("UPDATE servicios_reglas SET activo = 1 WHERE servicio_id = 3 AND codigo_regla = ?", (r,))
    for r in ['EXACTO_FINDES_MES', 'EXACTO_DIA_ESPECIFICO_MES']:
        cur.execute("UPDATE servicios_reglas SET activo = 0 WHERE servicio_id = 3 AND codigo_regla = ?", (r,))
        
    # Delete test adjustments
    rules_to_suspend = ['MAX_TURNOS', 'MAX_HORAS_MES_CALENDARIO', 'MIN_HORAS_MES_CALENDARIO', 'ASIGNACION_FIJA']
    for rule in rules_to_suspend:
        cur.execute("""
            DELETE FROM personal_reglas_ajustes 
            WHERE codigo_regla = ? AND accion = 'SUSPENDER' AND parametros_json = '{}'
            AND fecha_inicio = ? AND fecha_fin = ?
        """, (rule, FECHA_INICIO, FECHA_FIN))
        
    conn.commit()
    conn.close()
    print("\nDatabase settings restored.")

if __name__ == "__main__":
    try:
        ok_hard = run_test("Case 1: Unified EXACTO_FINDE_Y_DIA rule in HARD mode", mode="HARD")
        ok_soft = run_test("Case 2: Unified EXACTO_FINDE_Y_DIA rule in SOFT mode", mode="SOFT")
        
        if ok_hard and ok_soft:
            print("\n*** ALL UNIFIED RULE TESTS PASSED SUCCESSFULLY! ***")
        else:
            print("\n*** SOME TESTS FAILED! ***")
    finally:
        restore_rules()
