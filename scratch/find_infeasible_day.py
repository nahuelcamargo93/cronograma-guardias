import sqlite3
import os
import sys
import shutil
from datetime import datetime, date, timedelta
from ortools.sat.python import cp_model

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set temporary DB path
TEMP_DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "temp_find_day.db")
ORIG_DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cronograma_inteligente.db")

if os.path.exists(TEMP_DB):
    try: os.remove(TEMP_DB)
    except: pass
shutil.copyfile(ORIG_DB, TEMP_DB)

import database.connection
database.connection.DB_PATH = TEMP_DB

from database.data_loader import obtener_empleados, obtener_turnos
from database import queries as db_queries
from data import SERVICIO_ID, FECHA_INICIO, FECHA_FIN, FERIADOS
import hard_rules

def apply_fixes(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    new_exclusions = '{"turnos": ["06-12_Monitorista", "12-18_Monitorista", "18-24_Monitorista", "06-12_Supervisor", "12-18_Supervisor", "18-24_Supervisor"]}'
    cursor.execute("""
        UPDATE personal_reglas
        SET parametros_json = ?
        WHERE personal_nombre = 'GUERRIDO Noelia' AND codigo_regla = 'EXCLUIR_TURNOS'
    """, (new_exclusions,))
    
    # Check if hour adjustments already exist for Noelia, if not insert
    cursor.execute("SELECT 1 FROM personal_reglas_ajustes WHERE personal_nombre = 'GUERRIDO Noelia' AND codigo_regla = 'MIN_HORAS_MES_CALENDARIO'")
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo)
            VALUES 
            ('GUERRIDO Noelia', 'MIN_HORAS_MES_CALENDARIO', '2026-06-01', '2026-06-30', 'SOBRESCRIBIR', '{"min_horas": 114}', 1),
            ('GUERRIDO Noelia', 'MAX_HORAS_MES_CALENDARIO', '2026-06-01', '2026-06-30', 'SOBRESCRIBIR', '{"max_horas": 114}', 1)
        """)
    conn.commit()
    conn.close()

def main_diagnostic():
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
    
    args_modelo = [empleados, config_turnos, turnos_dict, demanda_req, adjustments_db, total_dias, feriados_indices, offset_dia, num_semanas, reglas_servicio_db, ajustes_reglas, historial_semana_previa, SERVICIO_ID]
    
    from debug_imposibilidad import construir_modelo_test, intentar_resolver
    
    print("Testing if base model is viable with COBERTURA_DINAMICA disabled...")
    modelo_no_cob = construir_modelo_test(*args_modelo, reglas_a_ignorar=['COBERTURA_DINAMICA'])
    if intentar_resolver(modelo_no_cob):
        print("Base model without COBERTURA_DINAMICA is FEASIBLE.")
    else:
        print("Base model without COBERTURA_DINAMICA is INFEASIBLE. Other rules are conflicting.")
        return

    # Monkeypatch hard_rules._aplicar_cobertura_dinamica
    orig_cobertura = hard_rules._aplicar_cobertura_dinamica
    
    def make_mock_cobertura(skip_dia):
        def mock(modelo, turnos_vars, empleados, demanda_req, database_ajustes, dias_del_bloque, feriados, offset_dia, turnos_dict, fecha_inicio_dt, historial, reglas_servicio, ajustes_reglas):
            # We call the original function, but we modify the range of days by intercepting or we just run the original logic but skip skip_dia.
            # Let's call the original logic but with a modified range or by filtering the days.
            # To do that, we can just temporarily replace the loop inside the logic by recreating it here:
            for dia in range(dias_del_bloque):
                if dia == skip_dia:
                    continue # Skip applying coverage constraints on this day
                
                # Original logic for 'dia'
                es_f = hard_rules._is_finde(dia, offset_dia, feriados)
                tipo_dia = "Finde_Feriado" if es_f else "Semana"
                fecha_actual_iso = (fecha_inicio_dt + timedelta(days=dia)).isoformat()
                dia_semana_actual = (dia + offset_dia) % 7
                
                candidates_by_window = {}
                for demanda in demanda_req.get(tipo_dia, []):
                    dias_sem = demanda.get("dias_semana")
                    applies = False
                    if dias_sem:
                        dias_validos = [int(x.strip()) for x in dias_sem.split(",") if x.strip().isdigit()]
                        if dia_semana_actual in dias_validos:
                            applies = True
                    else:
                        if dia in feriados:
                            applies = True
                        elif tipo_dia == "Semana" and dia_semana_actual in [0, 1, 2, 3, 4]:
                            applies = True
                        elif tipo_dia == "Finde_Feriado" and dia_semana_actual in [5, 6]:
                            applies = True
                            
                    if applies:
                        puesto_key = demanda.get("puesto_id")
                        key = (puesto_key, demanda["hora_inicio"], demanda["hora_fin"])
                        candidates_by_window.setdefault(key, []).append(demanda)
                        
                final_demandas = []
                for key, candidates in candidates_by_window.items():
                    especificas = [c for c in candidates if c.get("dias_semana")]
                    if especificas:
                        final_demandas.extend(especificas)
                    else:
                        final_demandas.extend(candidates)
                        
                demandas_por_ventana = {}
                for demanda in final_demandas:
                    key = (demanda["hora_inicio"], demanda["hora_fin"])
                    demandas_por_ventana.setdefault(key, []).append(demanda)
                    
                for (h_start, h_end), window_demands in demandas_por_ventana.items():
                    d_h_start = hard_rules.time_to_float(h_start)
                    d_h_end = hard_rules.time_to_float(h_end)
                    d_abs_start = dia * 24 + d_h_start
                    if d_h_end <= d_h_start and not (d_h_start == 0 and d_h_end == 0):
                        d_abs_end = (dia + 1) * 24 + d_h_end
                    elif d_h_end == 0 and d_h_start > 0:
                        d_abs_end = (dia + 1) * 24
                    else:
                        d_abs_end = dia * 24 + d_h_end
                        
                    planta_dem = None
                    residente_dem = None
                    otras_dems = []
                    for dem in window_demands:
                        if dem["puesto"] == "Planta":
                            planta_dem = dem
                        elif dem["puesto"] == "Residente":
                            residente_dem = dem
                        else:
                            otras_dems.append(dem)
                            
                    pool_planta_normales = []
                    pool_planta_extras = []
                    extra_planta_vars_in_window = []
                    pool_residente_normales = []
                    pool_residente_extras = []
                    has_planta_block_vars = False
                    has_residente_block_vars = False
                    
                    for emp in empleados:
                        fecha_bloque = (fecha_inicio_dt + timedelta(days=dia)).strftime("%Y-%m-%d")
                        params_extra = hard_rules._re.resolver_parametros_regla('PERSONAL_EXTRA_FUERA_MINIMO', emp.nombre, fecha_bloque, reglas_servicio_db, emp.reglas, ajustes_reglas)
                        is_special_extra = False
                        if hard_rules._re.regla_existe(params_extra) and isinstance(params_extra, dict):
                            nombres_extra_resueltos = params_extra.get('nombres', [])
                            if emp.nombre in nombres_extra_resueltos:
                                is_special_extra = True
                        
                        for d_off in [0, -1]:
                            dia_t = dia + d_off
                            if dia_t < 0:
                                if historial:
                                    prev_guards = historial.get(emp.nombre, [])
                                    fecha_ayer = (fecha_inicio_dt + timedelta(days=-1)).strftime("%Y-%m-%d")
                                    for g in prev_guards:
                                        if g['fecha'] == fecha_ayer:
                                            t_prev_nombre = g['turno']
                                            if t_prev_nombre in turnos_dict:
                                                t_info = turnos_dict[t_prev_nombre]
                                                ts_abs = -1 * 24 + hard_rules.time_to_float(t_info.hora_inicio)
                                                te_abs = ts_abs + t_info.horas
                                                if ts_abs <= d_abs_start + 0.01 and te_abs >= d_abs_end - 0.01:
                                                    if t_info.puesto_nombre == "Planta":
                                                        pool_planta_normales.append(1)
                                                        if is_special_extra:
                                                            extra_planta_vars_in_window.append(1)
                                                    elif t_info.puesto_nombre == "Residente":
                                                        pool_residente_normales.append(1)
                                continue
                                
                            if dia_t in emp.dias_licencia:
                                continue
                                
                            for t_nombre, t_info in turnos_dict.items():
                                if (emp.nombre, dia_t, t_nombre) in turnos_vars:
                                    ts_abs = dia_t * 24 + hard_rules.time_to_float(t_info.hora_inicio)
                                    te_abs = ts_abs + t_info.horas
                                    if ts_abs <= d_abs_start + 0.01 and te_abs >= d_abs_end - 0.01:
                                        var = turnos_vars[(emp.nombre, dia_t, t_nombre)]
                                        if t_info.puesto_nombre == "Planta":
                                            pool_planta_normales.append(var)
                                            if dia_t >= 0:
                                                has_planta_block_vars = True
                                            if is_special_extra:
                                                extra_planta_vars_in_window.append(var)
                                        elif t_info.puesto_nombre == "Residente":
                                            pool_residente_normales.append(var)
                                            if dia_t >= 0:
                                                has_residente_block_vars = True
                                                
                    if planta_dem:
                        p_min = planta_dem.get("cantidad_min")
                        p_max = planta_dem.get("cantidad_max")
                        aj_p = None
                        for (fi, ff), cambios in database_ajustes.items():
                            if fi <= fecha_actual_iso <= ff:
                                for adj in cambios:
                                    if adj["demanda_config_id"] == planta_dem["id"]:
                                        aj_p = adj
                                        break
                        if aj_p:
                            if aj_p["dias_override"]:
                                dias_validos = [int(x) for x in aj_p["dias_override"].split(",")]
                                if dia_semana_actual in dias_validos or dia in feriados:
                                    p_min = aj_p.get("cantidad_min")
                                    p_max = aj_p.get("cantidad_max")
                            else:
                                p_min = aj_p.get("cantidad_min")
                                p_max = aj_p.get("cantidad_max")
                        if p_min is not None and p_min > 0:
                            if d_abs_end <= 8 and not has_planta_block_vars: pass
                            else: modelo.Add(sum(pool_planta_normales) >= p_min)
                        if p_max is not None:
                            modelo.Add(sum(pool_planta_normales) <= p_max)
                            
                    if residente_dem:
                        r_min = residente_dem.get("cantidad_min")
                        r_max = residente_dem.get("cantidad_max")
                        aj_r = None
                        for (fi, ff), cambios in database_ajustes.items():
                            if fi <= fecha_actual_iso <= ff:
                                for adj in cambios:
                                    if adj["demanda_config_id"] == residente_dem["id"]:
                                        aj_r = adj
                                        break
                        if aj_r:
                            if aj_r["dias_override"]:
                                dias_validos = [int(x) for x in aj_r["dias_override"].split(",")]
                                if dia_semana_actual in dias_validos or dia in feriados:
                                    r_min = aj_r.get("cantidad_min")
                                    r_max = aj_r.get("cantidad_max")
                            else:
                                r_min = aj_r.get("cantidad_min")
                                r_max = aj_r.get("cantidad_max")
                        if r_min is not None and r_min > 0:
                            if d_abs_end <= 8 and not has_residente_block_vars: pass
                            else:
                                if extra_planta_vars_in_window:
                                    for var in extra_planta_vars_in_window:
                                        modelo.Add(sum(pool_residente_normales) >= r_min + var)
                                modelo.Add(sum(pool_residente_normales) >= r_min)
                        if r_max is not None:
                            modelo.Add(sum(pool_residente_normales) <= r_max)
                            
                    for dem in otras_dems:
                        c_min = dem.get("cantidad_min")
                        c_max = dem.get("cantidad_max")
                        aj_o = None
                        for (fi, ff), cambios in database_ajustes.items():
                            if fi <= fecha_actual_iso <= ff:
                                for adj in cambios:
                                    if adj["demanda_config_id"] == dem["id"]:
                                        aj_o = adj
                                        break
                        if aj_o:
                            if aj_o["dias_override"]:
                                dias_validos = [int(x) for x in aj_o["dias_override"].split(",")]
                                if dia_semana_actual in dias_validos or dia in feriados:
                                    c_min = aj_o.get("cantidad_min")
                                    c_max = aj_o.get("cantidad_max")
                            else:
                                c_min = aj_o.get("cantidad_min")
                                c_max = aj_o.get("cantidad_max")
                                
                        if c_min is None and c_max is None: continue
                        
                        pool_normales = []
                        pool_extras = []
                        has_block_vars = False
                        
                        for emp in empleados:
                            fecha_bloque = (fecha_inicio_dt + timedelta(days=dia)).strftime("%Y-%m-%d")
                            params_extra = hard_rules._re.resolver_parametros_regla('PERSONAL_EXTRA_FUERA_MINIMO', emp.nombre, fecha_bloque, reglas_servicio_db, emp.reglas, ajustes_reglas)
                            es_extra = False
                            if hard_rules._re.regla_existe(params_extra) and isinstance(params_extra, dict):
                                nombres_extra_resueltos = params_extra.get('nombres', [])
                                if emp.nombre in nombres_extra_resueltos:
                                    es_extra = True
                                    
                            for d_off in [0, -1]:
                                dia_t = dia + d_off
                                if dia_t < 0:
                                    if historial:
                                        prev_guards = historial.get(emp.nombre, [])
                                        fecha_ayer = (fecha_inicio_dt + timedelta(days=-1)).strftime("%Y-%m-%d")
                                        for g in prev_guards:
                                            if g['fecha'] == fecha_ayer:
                                                t_prev_nombre = g['turno']
                                                if t_prev_nombre in turnos_dict:
                                                    t_info = turnos_dict[t_prev_nombre]
                                                    ts_abs = -1 * 24 + hard_rules.time_to_float(t_info.hora_inicio)
                                                    te_abs = ts_abs + t_info.horas
                                                    if ts_abs <= d_abs_start + 0.01 and te_abs >= d_abs_end - 0.01:
                                                        if es_extra: pool_extras.append(1)
                                                        else: pool_normales.append(1)
                                    continue
                                    
                                if dia_t in emp.dias_licencia: continue
                                
                                for t_nombre, t_info in turnos_dict.items():
                                    if t_info.puesto_nombre != dem["puesto"]:
                                        continue
                                    if (emp.nombre, dia_t, t_nombre) in turnos_vars:
                                        ts_abs = dia_t * 24 + hard_rules.time_to_float(t_info.hora_inicio)
                                        te_abs = ts_abs + t_info.horas
                                        if ts_abs <= d_abs_start + 0.01 and te_abs >= d_abs_end - 0.01:
                                            if es_extra: pool_extras.append(turnos_vars[(emp.nombre, dia_t, t_nombre)])
                                            else:
                                                pool_normales.append(turnos_vars[(emp.nombre, dia_t, t_nombre)])
                                                if dia_t >= 0:
                                                    has_block_vars = True
                                                    
                        if c_min is not None and c_min > 0:
                            if d_abs_end <= 8 and not has_block_vars: pass
                            else: modelo.Add(sum(pool_normales) >= c_min)
                        if c_max is not None:
                            modelo.Add(sum(pool_normales) + sum(pool_extras) <= c_max)
        return mock
    
    print("\nStarting day-by-day bisection for COBERTURA_DINAMICA...")
    infeasible_days = []
    for d in range(total_dias):
        fecha_d = fecha_inicio_dt + timedelta(days=d)
        fecha_str = fecha_d.strftime("%Y-%m-%d")
        
        # Monkeypatch the coverage rule to skip day `d`
        hard_rules._aplicar_cobertura_dinamica = make_mock_cobertura(d)
        
        # Test feasibility
        modelo = construir_modelo_test(*args_modelo)
        is_feasible = intentar_resolver(modelo)
        
        if is_feasible:
            print(f"  [WARN] Skipping day {d} ({fecha_str}, weekday: {fecha_d.weekday()}) makes the model FEASIBLE!")
            infeasible_days.append((d, fecha_str))
            
    # Restore original function
    hard_rules._aplicar_cobertura_dinamica = orig_cobertura
    
    print("\n=== SUMMARY OF INFEASIBLE DAYS ===")
    if infeasible_days:
        for d, f_str in infeasible_days:
            print(f"Contradiction lies on date: {f_str} (day index: {d})")
    else:
        print("No single day could resolve the infeasibility when skipped.")

if __name__ == "__main__":
    try:
        main_diagnostic()
    finally:
        if os.path.exists(TEMP_DB):
            try:
                os.remove(TEMP_DB)
            except:
                pass
