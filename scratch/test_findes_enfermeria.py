import sys
sys.path.append('.')

import sqlite3
from datetime import date, timedelta
import json
from main import ejecutar_optimizacion
import rule_engine as _re

def test_rule():
    print("Running optimization for Servicio 2 (Enfermeria) in July 2026...")
    res = ejecutar_optimizacion(2, "2026-07-01", "2026-07-31", notas="Test FINDES_COMPLETOS_Y_MEDIOS")
    
    if res.get("status") != "success":
        print(f"ERROR: Optimization failed. Status/Error: {res}")
        return False
        
    cronograma_id = res["cronograma_id"]
    print(f"Optimization succeeded! Cronograma ID: {cronograma_id}\n")
    
    conn = sqlite3.connect('cronograma_inteligente.db')
    cur = conn.cursor()
    
    # 1. Load dates
    fecha_inicio_str = "2026-07-01"
    fecha_fin_str = "2026-07-31"
    fecha_inicio_dt = date.fromisoformat(fecha_inicio_str)
    fecha_fin_dt = date.fromisoformat(fecha_fin_str)
    dias_del_bloque = (fecha_fin_dt - fecha_inicio_dt).days + 1
    offset_dia = fecha_inicio_dt.weekday()
    
    # 2. Get feriados
    from data import FERIADOS
    feriados = []
    for f_str in FERIADOS:
        f_dt = date.fromisoformat(f_str)
        delta = (f_dt - fecha_inicio_dt).days
        if 0 <= delta < dias_del_bloque:
            feriados.append(delta)
            
    # 3. Group weekends (Saturdays and Sundays)
    findes = {}
    for d in range(dias_del_bloque):
        fecha_d = fecha_inicio_dt + timedelta(days=d)
        wd = fecha_d.weekday()
        if wd in (5, 6):
            lunes = (fecha_d - timedelta(days=wd)).isoformat()
            findes.setdefault(lunes, []).append((d, wd))
            
    # 4. Get rules service
    from database.queries import cargar_reglas_servicio, cargar_ajustes_reglas_personal
    reglas_servicio = cargar_reglas_servicio(2)
    ajustes_reglas = cargar_ajustes_reglas_personal(fecha_inicio_str, fecha_fin_str)
    
    # 5. Fetch employees
    cur.execute("SELECT nombre, rol, categoria FROM personal WHERE servicio_id = 2")
    employees = cur.fetchall()
    
    # Load licencias for each employee
    licencias_por_persona = {}
    for emp_nombre, _, _ in employees:
        cur.execute("SELECT tipo, fecha_inicio, fecha_fin FROM licencias WHERE nombre = ?", (emp_nombre,))
        lics = cur.fetchall()
        lic_dias = set()
        for tipo, fi, ff in lics:
            fi_dt = date.fromisoformat(fi)
            ff_dt = date.fromisoformat(ff)
            for d in range(dias_del_bloque):
                fecha_d = fecha_inicio_dt + timedelta(days=d)
                if fi_dt <= fecha_d <= ff_dt:
                    lic_dias.add(d)
        licencias_por_persona[emp_nombre] = lic_dias
        
    print(f"{'Empleado':<25} | {'Disp (k)':<8} | {'Target C':<8} | {'Actual C':<8} | {'Target M':<8} | {'Actual M':<8} | Result")
    print("-" * 90)
    
    all_ok = True
    
    for emp_nombre, _, emp_cat in employees:
        # Load rule parameters
        cur.execute("SELECT parametros_json FROM personal_reglas WHERE personal_nombre = ? AND codigo_regla = 'FINDES_COMPLETOS_Y_MEDIOS'", (emp_nombre,))
        rule_row = cur.fetchone()
        emp_reglas = {'FINDES_COMPLETOS_Y_MEDIOS': json.loads(rule_row[0])} if rule_row else {}
        
        params = _re.resolver_parametros_regla('FINDES_COMPLETOS_Y_MEDIOS', emp_nombre, fecha_inicio_str, reglas_servicio, emp_reglas, ajustes_reglas)
        if not _re.regla_existe(params) or _re.regla_suspendida(params):
            continue
            
        # Count k (available weekends)
        lic_dias = licencias_por_persona[emp_nombre]
        k = 0
        for lunes, dias_info in findes.items():
            dias_disponibles = 0
            for d, wd in dias_info:
                if d in lic_dias:
                    continue
                # Franco forzado check
                fecha_d_str = (fecha_inicio_dt + timedelta(days=d)).isoformat()
                p_franco = _re.resolver_parametros_regla('FRANCO_FORZADO', emp_nombre, fecha_d_str, reglas_servicio, emp_reglas, ajustes_reglas)
                if _re.regla_existe(p_franco) and not _re.regla_suspendida(p_franco):
                    continue
                dias_disponibles += 1
            if dias_disponibles > 0:
                k += 1
                
        # Resolve target
        por_disp = params.get('por_disponibilidad', {})
        conf = por_disp.get(str(k))
        if not conf:
            if k >= 5: conf = {"completos": 3, "medios": 1}
            elif k == 4: conf = {"completos": 2, "medios": 1}
            elif k == 3: conf = {"completos": 1, "medios": 1}
            elif k == 2: conf = {"completos": 1, "medios": 0}
            elif k == 1: conf = {"completos": 0, "medios": 1}
            else: conf = {"completos": 0, "medios": 0}
            
        target_c = conf.get('completos', 0)
        target_m = conf.get('medios', 0)
        
        # Calculate real bounds
        findes_completos_posibles = 0
        findes_medios_posibles = 0
        for lunes, dias_info in findes.items():
            d_sat = None
            d_sun = None
            for d, wd in dias_info:
                if wd == 5: d_sat = d
                elif wd == 6: d_sun = d
            if d_sat is None or d_sun is None:
                continue
            sat_ok = d_sat not in lic_dias
            if sat_ok:
                fecha_sat_str = (fecha_inicio_dt + timedelta(days=d_sat)).isoformat()
                p_f_sat = _re.resolver_parametros_regla('FRANCO_FORZADO', emp_nombre, fecha_sat_str, reglas_servicio, emp_reglas, ajustes_reglas)
                if _re.regla_existe(p_f_sat) and not _re.regla_suspendida(p_f_sat):
                    sat_ok = False
            sun_ok = d_sun not in lic_dias
            if sun_ok:
                fecha_sun_str = (fecha_inicio_dt + timedelta(days=d_sun)).isoformat()
                p_f_sun = _re.resolver_parametros_regla('FRANCO_FORZADO', emp_nombre, fecha_sun_str, reglas_servicio, emp_reglas, ajustes_reglas)
                if _re.regla_existe(p_f_sun) and not _re.regla_suspendida(p_f_sun):
                    sun_ok = False
            if sat_ok and sun_ok:
                findes_completos_posibles += 1
            if sat_ok or sun_ok:
                findes_medios_posibles += 1
                
        target_c_real = min(target_c, findes_completos_posibles)
        target_m_real = min(target_m, findes_medios_posibles - target_c_real)
        
        # Count actual from guardias table
        cur.execute("SELECT fecha, es_finde FROM guardias WHERE cronograma_id = ? AND nombre = ?", (cronograma_id, emp_nombre))
        guards = cur.fetchall()
        
        # Group actual guardias by weekend
        actual_work_by_weekend = {}
        for f_str, is_f in guards:
            f_dt = date.fromisoformat(f_str)
            wd = f_dt.weekday()
            if wd in (5, 6):
                lunes_w = (f_dt - timedelta(days=wd)).isoformat()
                actual_work_by_weekend.setdefault(lunes_w, set()).add(wd)
                
        actual_c = 0
        actual_m = 0
        for lunes_w, days_worked in actual_work_by_weekend.items():
            # A complete weekend is when they worked both Saturday (5) and Sunday (6)
            if 5 in days_worked and 6 in days_worked:
                actual_c += 1
            elif 5 in days_worked or 6 in days_worked:
                actual_m += 1
                
        status_str = "OK"
        if actual_c != target_c_real or actual_m != target_m_real:
            status_str = "FAIL"
            all_ok = False
            
        print(f"{emp_nombre:<25} | {k:<8} | {target_c_real:<8} | {actual_c:<8} | {target_m_real:<8} | {actual_m:<8} | {status_str}")
        
    conn.close()
    
    if all_ok:
        print("\nALL OK: FINDES_COMPLETOS_Y_MEDIOS rule is working perfectly!")
        return True
    else:
        print("\nFAIL: Some rules were not satisfied.")
        return False

if __name__ == "__main__":
    test_rule()
