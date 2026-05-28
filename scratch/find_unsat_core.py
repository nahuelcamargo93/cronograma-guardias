import sqlite3
import os
import sys
import shutil
from datetime import datetime, date, timedelta
from ortools.sat.python import cp_model

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set temporary DB path
TEMP_DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "temp_unsat_core.db")
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
    
    # Check if hour adjustments exist for Noelia, if not insert
    cursor.execute("SELECT 1 FROM personal_reglas_ajustes WHERE personal_nombre = 'GUERRIDO Noelia' AND codigo_regla = 'MIN_HORAS_MES_CALENDARIO'")
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo)
            VALUES 
            ('GUERRIDO Noelia', 'MIN_HORAS_MES_CALENDARIO', '2026-06-01', '2026-06-30', 'SOBRESCRIBIR', '{"min_horas": 114}', 1),
            ('GUERRIDO Noelia', 'MAX_HORAS_MES_CALENDARIO', '2026-06-01', '2026-06-30', 'SOBRESCRIBIR', '{"max_horas": 114}', 1)
        """)
        
    # Suspend FINDES_COMPLETOS_Y_MEDIOS for SUAREZ Carolina by updating the existing row
    cursor.execute("""
        UPDATE personal_reglas_ajustes
        SET accion = 'SUSPENDER'
        WHERE personal_nombre = 'SUAREZ Carolina' AND codigo_regla = 'FINDES_COMPLETOS_Y_MEDIOS'
    """)
    conn.commit()
    
    # Print it to debug
    rows = conn.execute("SELECT * FROM personal_reglas_ajustes WHERE personal_nombre = 'SUAREZ Carolina'").fetchall()
    print("DEBUG IN DB: adjustments for SUAREZ Carolina:", rows)
    
    conn.close()

def build_model_with_assumptions():
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
    print("DEBUG: ajustes_reglas for SUAREZ Carolina:", ajustes_reglas.get('SUAREZ Carolina'))
    empleados = obtener_empleados(SERVICIO_ID, FECHA_INICIO, total_dias)
    turnos_dict = obtener_turnos(SERVICIO_ID)
    historial_semana_previa = db_queries.cargar_guardias_previas(FECHA_INICIO, dias_atras=28, servicio_id=SERVICIO_ID)
    offset_dia = fecha_inicio_dt.weekday()
    
    # We will build our own CP model and add constraints with assumptions
    modelo = cp_model.CpModel()
    
    # 1. Variables
    turnos_vars = {}
    mapa_dias = {"Lunes": 0, "Martes": 1, "Miercoles": 2, "Jueves": 3, "Viernes": 4, "Sabado": 5, "Domingo": 6}
    
    for emp in empleados:
        nombre = emp.nombre
        rol_persona = emp.rol
        licencia_dias = emp.dias_licencia
        for dia in range(total_dias):
            dia_semana = (dia + offset_dia) % 7
            es_finde_o_feriado = (dia_semana >= 5) or (dia in feriados_indices)
            tipo_dia = "Finde_Feriado" if es_finde_o_feriado else "Semana"
            lista_turnos = config_turnos.get(tipo_dia, {}).keys()
            
            for t in lista_turnos:
                t_info = turnos_dict.get(t)
                puesto_nombre_turno = t_info.puesto_nombre if t_info else None
                
                if puesto_nombre_turno:
                    if emp.puestos_habilitados:
                        if puesto_nombre_turno not in emp.puestos_habilitados:
                            continue
                    else:
                        if rol_persona and rol_persona != "Rotativo" and rol_persona != puesto_nombre_turno:
                            continue
                            
                turnos_vars[(nombre, dia, t)] = modelo.NewBoolVar(f'turno_{nombre}_dia{dia}_{t}')
                
            # Limit: at most 1 shift per day
            vars_dia = [turnos_vars[(nombre, dia, t)] for t in lista_turnos if (nombre, dia, t) in turnos_vars]
            if vars_dia:
                modelo.Add(sum(vars_dia) <= 1)
                
    # We will define a dict to store our assumption variables and descriptions
    assumptions_dict = {}
    assumptions_list = []
    
    # Let's write helper to add assumption-controlled constraint
    def add_constrained(constraint, desc):
        lit = modelo.NewBoolVar(desc)
        modelo.Add(constraint).OnlyEnforceIf(lit)
        assumptions_dict[lit.Index()] = desc
        assumptions_list.append(lit)
        return lit

    # Apply licenses
    hard_rules._aplicar_licencias(modelo, turnos_vars, empleados, config_turnos, offset_dia, feriados_indices)
    
    # Apply Franco Forzado
    hard_rules._aplicar_franco_forzado(modelo, turnos_vars, empleados, total_dias, fecha_inicio_dt, config_turnos, reglas_servicio_db, ajustes_reglas)
    
    # Apply Max Horas Semana
    semanas_calendario = hard_rules._get_semanas_calendario(total_dias, fecha_inicio_dt)
    limite_horas_global = reglas_servicio_db.get('MAX_HORAS_SEMANA', {}).get('limite', 48)
    hard_rules._aplicar_limite_horas_semanales(modelo, turnos_vars, empleados, semanas_calendario, reglas_servicio_db, ajustes_reglas, historial_semana_previa, config_turnos, turnos_dict, offset_dia, feriados_indices, limite_horas_global)
    
    # Apply Descanso entre turnos
    hard_rules._aplicar_descanso_entre_turnos(modelo, turnos_vars, empleados, total_dias, fecha_inicio_dt, reglas_servicio_db, ajustes_reglas, offset_dia, feriados_indices, config_turnos, turnos_dict, historial_semana_previa)
    
    # Apply un solo turno por dia
    hard_rules._aplicar_un_solo_turno_por_dia(modelo, turnos_vars, empleados, total_dias, offset_dia, feriados_indices, fecha_inicio_dt, config_turnos, reglas_servicio_db, ajustes_reglas)
    
    # Apply personal asociado (We will control this with an assumption)
    params_asoc = hard_rules._re.resolver_parametros_regla('PERSONAL_ASOCIADO', 'GLOBAL', FECHA_INICIO, reglas_servicio_db, {}, {})
    if hard_rules._re.regla_existe(params_asoc) and not hard_rules._re.regla_suspendida(params_asoc):
        parejas = params_asoc.get('parejas', [])
        for p1_name, p2_name in parejas:
            emp_names = {e.nombre for e in empleados}
            if p1_name not in emp_names or p2_name not in emp_names:
                continue
            for d in range(total_dias):
                td = "Finde_Feriado" if hard_rules._is_finde(d, offset_dia, feriados_indices) else "Semana"
                lista_turnos = config_turnos.get(td, {}).keys()
                franjas = {}
                for t in lista_turnos:
                    t_info = turnos_dict.get(t)
                    if t_info:
                        key = (t_info.hora_inicio, t_info.horas)
                        franjas.setdefault(key, []).append(t)
                for key, turnos_franja in franjas.items():
                    vars1 = [turnos_vars[(p1_name, d, t)] for t in turnos_franja if (p1_name, d, t) in turnos_vars]
                    vars2 = [turnos_vars[(p2_name, d, t)] for t in turnos_franja if (p2_name, d, t) in turnos_vars]
                    add_constrained(sum(vars1) == sum(vars2), f"ASOCIADO_{p1_name}_{p2_name}_dia_{d}_franja_{key}")

    # Cobertura Dinamica: we will control coverage for each day with a separate assumption!
    for dia in range(total_dias):
        es_f = hard_rules._is_finde(dia, offset_dia, feriados_indices)
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
                if dia in feriados_indices:
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
            if especificas: final_demandas.extend(especificas)
            else: final_demandas.extend(candidates)
            
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
                if dem["puesto"] == "Planta": planta_dem = dem
                elif dem["puesto"] == "Residente": residente_dem = dem
                else: otras_dems.append(dem)
                
            # Gathering pools...
            pool_planta_normales = []
            extra_planta_vars_in_window = []
            pool_residente_normales = []
            
            for emp in empleados:
                fecha_bloque = (fecha_inicio_dt + timedelta(days=dia)).strftime("%Y-%m-%d")
                params_extra = hard_rules._re.resolver_parametros_regla('PERSONAL_EXTRA_FUERA_MINIMO', emp.nombre, fecha_bloque, reglas_servicio_db, emp.reglas, ajustes_reglas)
                is_special_extra = False
                if hard_rules._re.regla_existe(params_extra) and isinstance(params_extra, dict):
                    nombres_extra_resueltos = params_extra.get('nombres', [])
                    if emp.nombre in nombres_extra_resueltos: is_special_extra = True
                
                for d_off in [0, -1]:
                    dia_t = dia + d_off
                    if dia_t < 0:
                        if historial_semana_previa:
                            prev_guards = historial_semana_previa.get(emp.nombre, [])
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
                                                if is_special_extra: extra_planta_vars_in_window.append(1)
                                            elif t_info.puesto_nombre == "Residente":
                                                pool_residente_normales.append(1)
                        continue
                    if dia_t in emp.dias_licencia: continue
                    for t_nombre, t_info in turnos_dict.items():
                        if (emp.nombre, dia_t, t_nombre) in turnos_vars:
                            ts_abs = dia_t * 24 + hard_rules.time_to_float(t_info.hora_inicio)
                            te_abs = ts_abs + t_info.horas
                            if ts_abs <= d_abs_start + 0.01 and te_abs >= d_abs_end - 0.01:
                                var = turnos_vars[(emp.nombre, dia_t, t_nombre)]
                                if t_info.puesto_nombre == "Planta":
                                    pool_planta_normales.append(var)
                                    if is_special_extra: extra_planta_vars_in_window.append(var)
                                elif t_info.puesto_nombre == "Residente":
                                    pool_residente_normales.append(var)
                                    
            for dem in otras_dems:
                c_min = dem.get("cantidad_min")
                c_max = dem.get("cantidad_max")
                
                # Check adjustments
                aj_o = None
                for (fi, ff), cambios in adjustments_db.items():
                    if fi <= fecha_actual_iso <= ff:
                        for adj in cambios:
                            if adj["demanda_config_id"] == dem["id"]:
                                aj_o = adj
                                break
                if aj_o:
                    if aj_o["dias_override"]:
                        dias_validos = [int(x) for x in aj_o["dias_override"].split(",")]
                        if dia_semana_actual in dias_validos or dia in feriados_indices:
                            c_min = aj_o.get("cantidad_min")
                            c_max = aj_o.get("cantidad_max")
                    else:
                        c_min = aj_o.get("cantidad_min")
                        c_max = aj_o.get("cantidad_max")
                
                if c_min is None and c_max is None: continue
                
                pool_normales = []
                pool_extras = []
                for emp in empleados:
                    fecha_bloque = (fecha_inicio_dt + timedelta(days=dia)).strftime("%Y-%m-%d")
                    params_extra = hard_rules._re.resolver_parametros_regla('PERSONAL_EXTRA_FUERA_MINIMO', emp.nombre, fecha_bloque, reglas_servicio_db, emp.reglas, ajustes_reglas)
                    es_extra = False
                    if hard_rules._re.regla_existe(params_extra) and isinstance(params_extra, dict):
                        nombres_extra_resueltos = params_extra.get('nombres', [])
                        if emp.nombre in nombres_extra_resueltos: es_extra = True
                    for d_off in [0, -1]:
                        dia_t = dia + d_off
                        if dia_t < 0:
                            if historial_semana_previa:
                                prev_guards = historial_semana_previa.get(emp.nombre, [])
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
                            if t_info.puesto_nombre != dem["puesto"]: continue
                            if (emp.nombre, dia_t, t_nombre) in turnos_vars:
                                ts_abs = dia_t * 24 + hard_rules.time_to_float(t_info.hora_inicio)
                                te_abs = ts_abs + t_info.horas
                                if ts_abs <= d_abs_start + 0.01 and te_abs >= d_abs_end - 0.01:
                                    if es_extra: pool_extras.append(turnos_vars[(emp.nombre, dia_t, t_nombre)])
                                    else: pool_normales.append(turnos_vars[(emp.nombre, dia_t, t_nombre)])
                                    
                if c_min is not None and c_min > 0:
                    add_constrained(sum(pool_normales) >= c_min, f"COBERTURA_MIN_dia_{dia}_puesto_{dem['puesto']}_slot_{h_start}_{h_end}")
                if c_max is not None:
                    add_constrained(sum(pool_normales) + sum(pool_extras) <= c_max, f"COBERTURA_MAX_dia_{dia}_puesto_{dem['puesto']}_slot_{h_start}_{h_end}")

    # Hour limits (Controlled by assumptions)
    for emp in empleados:
        for m_key, dias_m in weeks_by_month(total_dias, fecha_inicio_dt).items():
            ref_date = (fecha_inicio_dt + timedelta(days=dias_m[0])).isoformat()
            p_min = hard_rules._re.resolver_parametros_regla('MIN_HORAS_MES_CALENDARIO', emp.nombre, ref_date, reglas_servicio_db, emp.reglas, ajustes_reglas)
            p_max = hard_rules._re.resolver_parametros_regla('MAX_HORAS_MES_CALENDARIO', emp.nombre, ref_date, reglas_servicio_db, emp.reglas, ajustes_reglas)
            
            vars_h = []
            for d in dias_m:
                td = "Finde_Feriado" if hard_rules._is_finde(d, offset_dia, feriados_indices) else "Semana"
                for t in config_turnos.get(td, {}).keys():
                    if (emp.nombre, d, t) in turnos_vars:
                        h_turno = turnos_dict[t].horas
                        vars_h.append(turnos_vars[(emp.nombre, d, t)] * h_turno)
            
            dias_lic = [d for d in dias_m if d in emp.dias_licencia]
            p_cred = hard_rules._re.resolver_parametros_regla('CREDITO_HORARIO_LICENCIA', emp.nombre, ref_date, reglas_servicio_db, emp.reglas, ajustes_reglas)
            h_sem = p_cred.get('horas_por_semana', 36) if hard_rules._re.regla_existe(p_cred) else 36
            horas_lic = int((h_sem / 7.0) * len(dias_lic) + 0.5)
            
            if hard_rules._re.regla_existe(p_min) and not hard_rules._re.regla_suspendida(p_min):
                min_h = p_min.get('min_horas', 144)
                piso = int((min_h / total_dias) * len(dias_m) + 0.5)
                if vars_h:
                    add_constrained(sum(vars_h) + horas_lic >= piso, f"MIN_HORAS_{emp.nombre}_{m_key}")
                    
            if hard_rules._re.regla_existe(p_max) and not hard_rules._re.regla_suspendida(p_max):
                max_h = p_max.get('max_horas', 144)
                tope = int((max_h / total_dias) * len(dias_m) + 0.5)
                if vars_h:
                    add_constrained(sum(vars_h) + horas_lic <= tope, f"MAX_HORAS_{emp.nombre}_{m_key}")

    # Weekend rules (controlled by assumptions)
    # Replicate min findes & exact findes & findes completos/medios...
    # Since findes completos is the active one, let's replicate findes completos rule
    for emp in empleados:
        if emp.nombre == 'SUAREZ Carolina':
            params_fcm_debug = hard_rules._re.resolver_parametros_regla('FINDES_COMPLETOS_Y_MEDIOS', emp.nombre, FECHA_INICIO, reglas_servicio_db, emp.reglas, ajustes_reglas)
            print(f"DEBUG SUAREZ: params={params_fcm_debug}, existe={hard_rules._re.regla_existe(params_fcm_debug)}, suspendida={hard_rules._re.regla_suspendida(params_fcm_debug)}")
            
        params_fcm = hard_rules._re.resolver_parametros_regla('FINDES_COMPLETOS_Y_MEDIOS', emp.nombre, FECHA_INICIO, reglas_servicio_db, emp.reglas, ajustes_reglas)
        if hard_rules._re.regla_existe(params_fcm) and not hard_rules._re.regla_suspendida(params_fcm):
            findes = {}
            for d in range(total_dias):
                fecha_d = fecha_inicio_dt + timedelta(days=d)
                wd = fecha_d.weekday()
                if wd in (5, 6):
                    lunes = (fecha_d - timedelta(days=wd)).isoformat()
                    findes.setdefault(lunes, []).append((d, wd))
            
            # Simple check
            k = 0
            for lunes, dias_info in findes.items():
                dias_disponibles = 0
                for d, wd in dias_info:
                    if d in emp.dias_licencia: continue
                    fecha_d_str = (fecha_inicio_dt + timedelta(days=d)).isoformat()
                    p_franco = hard_rules._re.resolver_parametros_regla('FRANCO_FORZADO', emp.nombre, fecha_d_str, reglas_servicio_db, emp.reglas, ajustes_reglas)
                    if hard_rules._re.regla_existe(p_franco) and not hard_rules._re.regla_suspendida(p_franco): continue
                    dias_disponibles += 1
                if dias_disponibles > 0: k += 1
            
            por_disp = params_fcm.get('por_disponibilidad', {})
            conf = por_disp.get(str(k), {"completos": 0, "medios": 0})
            target_completos = conf.get('completos', 0)
            target_medios = conf.get('medios', 0)
            
            findes_completos_posibles = 0
            findes_medios_posibles = 0
            vars_completo = []
            vars_medio = []
            
            for lunes, dias_info in findes.items():
                d_sat = None
                d_sun = None
                for d, wd in dias_info:
                    if wd == 5: d_sat = d
                    elif wd == 6: d_sun = d
                if d_sat is None or d_sun is None: continue
                
                sat_disp = d_sat not in emp.dias_licencia
                sun_disp = d_sun not in emp.dias_licencia
                
                if sat_disp and sun_disp: findes_completos_posibles += 1
                if sat_disp or sun_disp: findes_medios_posibles += 1
                
                pool_sat = [turnos_vars[(emp.nombre, d_sat, t)] for t in config_turnos.get("Finde_Feriado", {}).keys() if (emp.nombre, d_sat, t) in turnos_vars]
                v_sabado = modelo.NewBoolVar(f'traba_sat_{emp.nombre}_{lunes}')
                if pool_sat: modelo.AddMaxEquality(v_sabado, pool_sat)
                else: modelo.Add(v_sabado == 0)
                
                pool_sun = [turnos_vars[(emp.nombre, d_sun, t)] for t in config_turnos.get("Finde_Feriado", {}).keys() if (emp.nombre, d_sun, t) in turnos_vars]
                v_domingo = modelo.NewBoolVar(f'traba_dom_{emp.nombre}_{lunes}')
                if pool_sun: modelo.AddMaxEquality(v_domingo, pool_sun)
                else: modelo.Add(v_domingo == 0)
                
                v_completo = modelo.NewBoolVar(f'f_completo_{emp.nombre}_{lunes}')
                modelo.AddMinEquality(v_completo, [v_sabado, v_domingo])
                vars_completo.append(v_completo)
                
                v_medio = modelo.NewBoolVar(f'f_medio_{emp.nombre}_{lunes}')
                modelo.Add(v_sabado + v_domingo - 2 * v_completo == v_medio)
                vars_medio.append(v_medio)
                
            target_completos_real = min(target_completos, findes_completos_posibles)
            target_medios_real = min(target_medios, findes_medios_posibles - target_completos_real)
            
            if vars_completo:
                add_constrained(sum(vars_completo) == target_completos_real, f"FINDE_COMPLETO_{emp.nombre}")
            if vars_medio:
                add_constrained(sum(vars_medio) == target_medios_real, f"FINDE_MEDIO_{emp.nombre}")

    return modelo, assumptions_dict, assumptions_list

def weeks_by_month(dias_del_bloque, fecha_inicio_dt):
    meses = {}
    for d in range(dias_del_bloque):
        m_key = (fecha_inicio_dt + timedelta(days=d)).strftime("%Y-%m")
        meses.setdefault(m_key, []).append(d)
    return meses

def run_solver():
    modelo, assumptions_dict, assumptions = build_model_with_assumptions()
    
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 15
    
    # We will solve with all assumptions set to True
    modelo.AddAssumptions(assumptions)
    status = solver.Solve(modelo)
    
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print("SUCCESS: Model is FEASIBLE with all assumptions!")
    elif status == cp_model.INFEASIBLE:
        print("INFEASIBLE: Core conflicts isolated:")
        core = solver.SufficientAssumptionsForInfeasibility()
        for c in core:
            print(f"  Conflict: {assumptions_dict[c]}")
    else:
        print(f"Solver status: {status}")

if __name__ == "__main__":
    try:
        run_solver()
    finally:
        if os.path.exists(TEMP_DB):
            try: os.remove(TEMP_DB)
            except: pass
