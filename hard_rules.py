from datetime import date, timedelta
from typing import List, Dict, Any, Set
import math
import rule_engine as _re
from models import Empleado, Turno
from utils import time_to_float
from data import FECHA_INICIO, FECHA_FIN, DEBUG_LOGS, DEBUG_DISABLE_MAX_HORAS

def _get_semanas_calendario(dias_del_bloque: int, fecha_inicio_dt: date) -> Dict[tuple, List[tuple]]:
    semanas = {}
    for d in range(dias_del_bloque):
        fecha_d = fecha_inicio_dt + timedelta(days=d)
        iso_year, iso_week, iso_weekday = fecha_d.isocalendar()
        semanas.setdefault((iso_year, iso_week), []).append((d, fecha_d))
    return semanas

def _is_finde(d: int, offset_dia: int, feriados: List[int]) -> bool:
    return ((d + offset_dia) % 7) >= 5 or d in feriados

def aplicar_reglas_duras(
    modelo,
    turnos_vars,
    empleados: List[Empleado],
    demanda_turnos: Dict,
    turnos_dict: Dict[str, Turno],
    demanda_req: Dict,
    ajustes_demanda: Dict,
    dias_del_bloque: int,
    feriados: List[int],
    offset_dia: int,
    num_semanas: int,
    historial_semana_previa: Dict[str, List[Dict]],
    reglas_servicio: Dict[str, Any],
    ajustes_reglas_personal: Dict[str, Any],
    servicio_id: int
):
    fecha_inicio_dt = date.fromisoformat(FECHA_INICIO)
    semanas_calendario = _get_semanas_calendario(dias_del_bloque, fecha_inicio_dt)

    if 'MAX_HORAS_SEMANA' not in reglas_servicio:
        raise ValueError("❌ ERROR CRÍTICO: La regla 'MAX_HORAS_SEMANA' no está configurada en la BD.")
    limite_horas_global = reglas_servicio['MAX_HORAS_SEMANA'].get('limite', 48)

    _aplicar_licencias(modelo, turnos_vars, empleados, demanda_turnos, offset_dia, feriados)
    _aplicar_max_turnos(modelo, turnos_vars, empleados, semanas_calendario, reglas_servicio, ajustes_reglas_personal, historial_semana_previa)
    _aplicar_excluir_turnos(modelo, turnos_vars, empleados, dias_del_bloque, offset_dia, fecha_inicio_dt, reglas_servicio, ajustes_reglas_personal)
    _aplicar_min_turnos(modelo, turnos_vars, empleados, semanas_calendario, reglas_servicio, ajustes_reglas_personal, historial_semana_previa)
    _aplicar_cobertura_dinamica(modelo, turnos_vars, empleados, demanda_req, ajustes_demanda, dias_del_bloque, feriados, offset_dia, turnos_dict, fecha_inicio_dt, historial_semana_previa)
    _aplicar_limite_horas_semanales(modelo, turnos_vars, empleados, semanas_calendario, reglas_servicio, ajustes_reglas_personal, historial_semana_previa, demanda_turnos, turnos_dict, offset_dia, feriados, limite_horas_global)
    _aplicar_descanso_entre_turnos(modelo, turnos_vars, empleados, dias_del_bloque, fecha_inicio_dt, reglas_servicio, ajustes_reglas_personal, offset_dia, feriados, demanda_turnos, turnos_dict)
    _aplicar_un_solo_turno_por_dia(modelo, turnos_vars, empleados, dias_del_bloque, offset_dia, feriados, fecha_inicio_dt, demanda_turnos, reglas_servicio, ajustes_reglas_personal)
    _aplicar_max_horas_mes_calendario(modelo, turnos_vars, empleados, dias_del_bloque, offset_dia, feriados, fecha_inicio_dt, demanda_turnos, turnos_dict, reglas_servicio, ajustes_reglas_personal)
    _aplicar_fin_licencia(modelo, turnos_vars, empleados, dias_del_bloque, offset_dia, feriados, demanda_turnos)
    _aplicar_min_horas_mes_calendario(modelo, turnos_vars, empleados, dias_del_bloque, offset_dia, feriados, fecha_inicio_dt, demanda_turnos, turnos_dict, reglas_servicio, ajustes_reglas_personal)

def _aplicar_licencias(modelo, turnos_vars, empleados: List[Empleado], demanda_turnos, offset_dia, feriados):
    for emp in empleados:
        for d in emp.dias_licencia:
            for td in ["Semana", "Finde_Feriado"]:
                for t in demanda_turnos.get(td, {}).keys():
                    if (emp.nombre, d, t) in turnos_vars:
                        modelo.Add(turnos_vars[(emp.nombre, d, t)] == 0)

def _aplicar_max_turnos(modelo, turnos_vars, empleados, semanas_calendario, reglas_servicio, ajustes_reglas, historial):
    for emp in empleados:
        hist_emp = historial.get(emp.nombre, []) if historial else []
        for (iso_year, iso_week), days in semanas_calendario.items():
            first_day_of_week = days[0][1]
            fecha_lunes = (first_day_of_week - timedelta(days=first_day_of_week.isocalendar()[2] - 1)).isoformat()
            
            params = _re.resolver_parametros_regla('MAX_TURNOS', emp.nombre, fecha_lunes, reglas_servicio, emp.reglas, ajustes_reglas)
            if not _re.regla_existe(params) or not isinstance(params, list):
                continue

            prev_en_sem = [h for h in hist_emp if date.fromisoformat(h['fecha']).isocalendar()[:2] == (iso_year, iso_week)]
            for rest in params:
                t_tipo = rest.get('turno')
                max_sem = rest.get('max_por_semana', 99)
                if not t_tipo: continue
                
                prev_tipo = sum(1 for h in prev_en_sem if h['turno'] == t_tipo)
                v_tipo = [turnos_vars[(emp.nombre, d, t_tipo)] for d, fd in days if (emp.nombre, d, t_tipo) in turnos_vars]
                if v_tipo or prev_tipo > 0:
                    modelo.Add(sum(v_tipo) + prev_tipo <= max_sem)

def _aplicar_excluir_turnos(modelo, turnos_vars, empleados, dias_del_bloque, offset_dia, fecha_inicio_dt, reglas_servicio, ajustes_reglas):
    for emp in empleados:
        for d in range(dias_del_bloque):
            fecha_d = (fecha_inicio_dt + timedelta(days=d)).isoformat()
            params = _re.resolver_parametros_regla('EXCLUIR_TURNOS', emp.nombre, fecha_d, reglas_servicio, emp.reglas, ajustes_reglas)
            if not _re.regla_existe(params) or not isinstance(params, list):
                continue
            
            dia_semana = (d + offset_dia) % 7
            for excl in params:
                t_prohibidos = excl.get('turnos', [])
                d_prohibidos = excl.get('dias', [0,1,2,3,4,5,6])
                if dia_semana in d_prohibidos:
                    for tp in t_prohibidos:
                        if (emp.nombre, d, tp) in turnos_vars:
                            modelo.Add(turnos_vars[(emp.nombre, d, tp)] == 0)

def _aplicar_min_turnos(modelo, turnos_vars, empleados, semanas_calendario, reglas_servicio, ajustes_reglas, historial):
    for emp in empleados:
        hist_emp = historial.get(emp.nombre, []) if historial else []
        for (iso_year, iso_week), days in semanas_calendario.items():
            first_day_of_week = days[0][1]
            fecha_lunes = (first_day_of_week - timedelta(days=first_day_of_week.isocalendar()[2] - 1)).isoformat()

            params = _re.resolver_parametros_regla('MIN_TURNOS', emp.nombre, fecha_lunes, reglas_servicio, emp.reglas, ajustes_reglas)
            if not _re.regla_existe(params) or not isinstance(params, list):
                continue

            prev_en_sem = [h for h in hist_emp if date.fromisoformat(h['fecha']).isocalendar()[:2] == (iso_year, iso_week)]
            for rest in params:
                t_tipo = rest.get('turno')
                min_sem = rest.get('min_por_semana', 0)
                if not t_tipo or min_sem <= 0: continue
                
                prev_tipo = sum(1 for h in prev_en_sem if h['turno'] == t_tipo)
                v_tipo = [turnos_vars[(emp.nombre, d, t_tipo)] for d, fd in days if (emp.nombre, d, t_tipo) in turnos_vars and d not in emp.dias_licencia]
                
                if v_tipo:
                    min_efectivo = min(min_sem, len(v_tipo) + prev_tipo)
                    modelo.Add(sum(v_tipo) + prev_tipo >= min_efectivo)

def _aplicar_cobertura_dinamica(modelo, turnos_vars, empleados, demanda_req, ajustes_demanda, dias_del_bloque, feriados, offset_dia, turnos_dict, fecha_inicio_dt, historial):
    for dia in range(dias_del_bloque):
        es_f = _is_finde(dia, offset_dia, feriados)
        tipo_dia = "Finde_Feriado" if es_f else "Semana"
        fecha_actual_iso = (fecha_inicio_dt + timedelta(days=dia)).isoformat()
        dia_semana_actual = (dia + offset_dia) % 7
        
        for demanda in demanda_req.get(tipo_dia, []):
            cantidad_min = demanda.get("cantidad_min")
            cantidad_max = demanda.get("cantidad_max")
            
            ajuste_encontrado = None
            for (fi, ff), cambios in ajustes_demanda.items():
                if fi <= fecha_actual_iso <= ff:
                    for adj in cambios:
                        if adj["demanda_config_id"] == demanda["id"]:
                            ajuste_encontrado = adj
                            break
            
            if ajuste_encontrado:
                if ajuste_encontrado["dias_override"]:
                    dias_validos = [int(x) for x in ajuste_encontrado["dias_override"].split(",")]
                    if dia_semana_actual not in dias_validos and dia not in feriados:
                        cantidad_min, cantidad_max = 0, 0
                    else:
                        cantidad_min = ajuste_encontrado.get("cantidad_min")
                        cantidad_max = ajuste_encontrado.get("cantidad_max")
                else:
                    cantidad_min = ajuste_encontrado.get("cantidad_min")
                    cantidad_max = ajuste_encontrado.get("cantidad_max")
            
            if (not cantidad_min) and (not cantidad_max): continue
            
            pool_vars = []
            d_h_start = time_to_float(demanda["hora_inicio"])
            d_h_end = time_to_float(demanda["hora_fin"])
            d_abs_start = dia * 24 + d_h_start
            
            if d_h_end <= d_h_start and not (d_h_start == 0 and d_h_end == 0):
                d_abs_end = (dia + 1) * 24 + d_h_end
            elif d_h_end == 0 and d_h_start > 0:
                d_abs_end = (dia + 1) * 24
            else:
                d_abs_end = dia * 24 + d_h_end

            for emp in empleados:
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
                                        ts_abs = -1 * 24 + time_to_float(t_info.hora_inicio)
                                        te_abs = ts_abs + t_info.horas
                                        if ts_abs <= d_abs_start + 0.01 and te_abs >= d_abs_end - 0.01:
                                            pool_vars.append(1)
                        continue

                    if dia_t in emp.dias_licencia: continue

                    for t_nombre, t_info in turnos_dict.items():
                        # Solo sumar turnos que pertenezcan al mismo puesto de la demanda
                        if t_info.puesto_nombre != demanda["puesto"]:
                            continue
                            
                        if (emp.nombre, dia_t, t_nombre) in turnos_vars:
                            # Filtro heurístico de Puesto usando la lógica vieja o simplemente evaluando hora
                            ts_abs = dia_t * 24 + time_to_float(t_info.hora_inicio)
                            te_abs = ts_abs + t_info.horas
                            if ts_abs <= d_abs_start + 0.01 and te_abs >= d_abs_end - 0.01:
                                pool_vars.append(turnos_vars[(emp.nombre, dia_t, t_nombre)])

            if cantidad_min is not None and cantidad_min > 0:
                if dia == 0 and time_to_float(demanda["hora_fin"]) <= 8: pass
                else: modelo.Add(sum(pool_vars) >= cantidad_min)
            
            if cantidad_max is not None:
                modelo.Add(sum(pool_vars) <= cantidad_max)

def _aplicar_limite_horas_semanales(modelo, turnos_vars, empleados, semanas_calendario, reglas_servicio, ajustes_reglas, historial, demanda_turnos, turnos_dict, offset_dia, feriados, limite_global):
    if DEBUG_DISABLE_MAX_HORAS: return
    for emp in empleados:
        hist_emp = historial.get(emp.nombre, []) if historial else []
        for (iso_year, iso_week), days in semanas_calendario.items():
            first_day_of_week = days[0][1]
            fecha_lunes = (first_day_of_week - timedelta(days=first_day_of_week.isocalendar()[2] - 1)).isoformat()
            
            prev_en_sem = [h for h in hist_emp if date.fromisoformat(h['fecha']).isocalendar()[:2] == (iso_year, iso_week)]
            horas_previas = sum(h['horas'] for h in prev_en_sem)
            
            horas_semanales = []
            for d, fd in days:
                es_f = _is_finde(d, offset_dia, feriados)
                td = "Finde_Feriado" if es_f else "Semana"
                for t in demanda_turnos.get(td, {}).keys():
                    if (emp.nombre, d, t) in turnos_vars:
                        h_turno = turnos_dict[t].horas if t in turnos_dict else 6
                        horas_semanales.append(turnos_vars[(emp.nombre, d, t)] * h_turno)
                        
            if horas_semanales or horas_previas > 0:
                params = _re.resolver_parametros_regla('MAX_HORAS_SEMANA', emp.nombre, fecha_lunes, reglas_servicio, emp.reglas, ajustes_reglas)
                if _re.regla_existe(params):
                    limite = params.get('limite', limite_global) if isinstance(params, dict) else limite_global
                    modelo.Add(sum(horas_semanales) + horas_previas <= limite)

def _aplicar_descanso_entre_turnos(modelo, turnos_vars, empleados, dias_del_bloque, fecha_inicio_dt, reglas_servicio, ajustes_reglas, offset_dia, feriados, demanda_turnos, turnos_dict):
    for emp in empleados:
        for d in range(dias_del_bloque - 1):
            fecha_d = (fecha_inicio_dt + timedelta(days=d)).isoformat()
            params = _re.resolver_parametros_regla('DESCANSO_ENTRE_TURNOS', emp.nombre, fecha_d, reglas_servicio, emp.reglas, ajustes_reglas)
            if not _re.regla_existe(params): continue
            
            config_descanso = params.get('por_turno')
            td_hoy = "Finde_Feriado" if _is_finde(d, offset_dia, feriados) else "Semana"
            turnos_hoy = [t for t in demanda_turnos.get(td_hoy, {}).keys() if (emp.nombre, d, t) in turnos_vars]
            
            for t1 in turnos_hoy:
                if t1 not in turnos_dict: continue
                t1_info = turnos_dict[t1]
                min_descanso = None
                if config_descanso:
                    for k, v in config_descanso.items():
                        if k in t1:
                            min_descanso = v; break
                if not min_descanso: continue
                
                t1_end = time_to_float(t1_info.hora_inicio) + t1_info.horas
                max_dias_futuro = math.ceil(min_descanso / 24) + 1
                for d_fut in range(d + 1, min(d + max_dias_futuro, dias_del_bloque)):
                    td_fut = "Finde_Feriado" if _is_finde(d_fut, offset_dia, feriados) else "Semana"
                    turnos_man = [t for t in demanda_turnos.get(td_fut, {}).keys() if (emp.nombre, d_fut, t) in turnos_vars]
                    for t2 in turnos_man:
                        if t2 not in turnos_dict: continue
                        t2_start = (d_fut - d) * 24 + time_to_float(turnos_dict[t2].hora_inicio)
                        if t2_start - t1_end < min_descanso - 0.01:
                            modelo.Add(turnos_vars[(emp.nombre, d, t1)] + turnos_vars[(emp.nombre, d_fut, t2)] <= 1)

def _aplicar_un_solo_turno_por_dia(modelo, turnos_vars, empleados, dias_del_bloque, offset_dia, feriados, fecha_inicio_dt, demanda_turnos, reglas_servicio, ajustes_reglas):
    mapa_dias = {"Lunes": 0, "Martes": 1, "Miercoles": 2, "Jueves": 3, "Viernes": 4, "Sabado": 5, "Domingo": 6}
    for emp in empleados:
        for d in range(dias_del_bloque):
            td = "Finde_Feriado" if _is_finde(d, offset_dia, feriados) else "Semana"
            dia_semana = (d + offset_dia) % 7
            fecha_d = (fecha_inicio_dt + timedelta(days=d)).isoformat()
            
            fijos_hoy = 0
            params = _re.resolver_parametros_regla('ASIGNACION_FIJA', emp.nombre, fecha_d, reglas_servicio, emp.reglas, ajustes_reglas)
            if _re.regla_existe(params) and isinstance(params, list):
                for asig in params:
                    if mapa_dias.get(asig.get('Dia')) == dia_semana: fijos_hoy += 1
            
            max_t = max(1, fijos_hoy)
            todos = [turnos_vars[(emp.nombre, d, t)] for t in demanda_turnos.get(td, {}).keys() if (emp.nombre, d, t) in turnos_vars]
            if todos: modelo.Add(sum(todos) <= max_t)

def _aplicar_max_horas_mes_calendario(modelo, turnos_vars, empleados, dias_del_bloque, offset_dia, feriados, fecha_inicio_dt, demanda_turnos, turnos_dict, reglas_servicio, ajustes_reglas):
    from data import FECHA_INICIO
    for emp in empleados:
        # Primero agrupar días por mes para aplicar el tope mensual correspondiente
        meses = {}
        for d in range(dias_del_bloque):
            m_key = (fecha_inicio_dt + timedelta(days=d)).strftime("%Y-%m")
            meses.setdefault(m_key, []).append(d)
            
        for m_key, dias_m in meses.items():
            # Resolver parámetros para el mes específico (usando el primer día del mes en el bloque)
            ref_date = (fecha_inicio_dt + timedelta(days=dias_m[0])).isoformat()
            params = _re.resolver_parametros_regla('MAX_HORAS_MES_CALENDARIO', emp.nombre, ref_date, reglas_servicio, emp.reglas, ajustes_reglas)
            
            if not _re.regla_suspendida(params):
                max_h = params.get('max_horas', 144) if isinstance(params, dict) else 144
                vars_h = []
                for d in dias_m:
                    td = "Finde_Feriado" if _is_finde(d, offset_dia, feriados) else "Semana"
                    for t in demanda_turnos.get(td, {}).keys():
                        if (emp.nombre, d, t) in turnos_vars:
                            h_turno = turnos_dict[t].horas if t in turnos_dict else 6
                            vars_h.append(turnos_vars[(emp.nombre, d, t)] * h_turno)
                
                dias_lic = [d for d in dias_m if d in emp.dias_licencia]
                # --- NUEVA LÓGICA DE CRÉDITO POR LICENCIA ---
                p_cred = _re.resolver_parametros_regla('CREDITO_HORARIO_LICENCIA', emp.nombre, ref_date, reglas_servicio, emp.reglas, ajustes_reglas)
                if _re.regla_existe(p_cred):
                    h_sem = p_cred.get('horas_por_semana', 36)
                    horas_lic = int((h_sem / 7.0) * len(dias_lic) + 0.5)
                else:
                    # Fallback proporcional (Enfermería)
                    horas_lic = int((float(max_h) / dias_del_bloque) * len(dias_lic) + 0.5)
                
                tope = int((max_h / dias_del_bloque) * len(dias_m) + 0.5)
                
                if vars_h:
                    modelo.Add(sum(vars_h) + horas_lic <= tope)

def _aplicar_fin_licencia(modelo, turnos_vars, empleados, dias_del_bloque, offset_dia, feriados, demanda_turnos):
    for emp in empleados:
        for d in range(dias_del_bloque - 1):
            if d in emp.dias_licencia and (d+1) not in emp.dias_licencia:
                td_sig = "Finde_Feriado" if _is_finde(d+1, offset_dia, feriados) else "Semana"
                vars_man = [turnos_vars[(emp.nombre, d+1, t)] for t in demanda_turnos.get(td_sig, {}).keys() if (emp.nombre, d+1, t) in turnos_vars]
                if vars_man: modelo.Add(sum(vars_man) >= 1)

def _aplicar_min_horas_mes_calendario(modelo, turnos_vars, empleados, dias_del_bloque, offset_dia, feriados, fecha_inicio_dt, demanda_turnos, turnos_dict, reglas_servicio, ajustes_reglas):
    from data import FECHA_INICIO
    for emp in empleados:
        # Agrupar días por mes
        meses = {}
        for d in range(dias_del_bloque):
            m_key = (fecha_inicio_dt + timedelta(days=d)).strftime("%Y-%m")
            meses.setdefault(m_key, []).append(d)
            
        for m_key, dias_m in meses.items():
            # Resolver parámetros para el mes específico
            ref_date = (fecha_inicio_dt + timedelta(days=dias_m[0])).isoformat()
            p_min = _re.resolver_parametros_regla('MIN_HORAS_MES_CALENDARIO', emp.nombre, ref_date, reglas_servicio, emp.reglas, ajustes_reglas)
            p_max = _re.resolver_parametros_regla('MAX_HORAS_MES_CALENDARIO', emp.nombre, ref_date, reglas_servicio, emp.reglas, ajustes_reglas)
            
            if _re.regla_existe(p_min) and not _re.regla_suspendida(p_min):
                min_h = p_min.get('min_horas', 144) if isinstance(p_min, dict) else 144
                
                # Si hay un tope máximo definido, el mínimo no puede ser mayor que el máximo
                if not _re.regla_suspendida(p_max):
                    max_h_ref = p_max.get('max_horas', 192) if isinstance(p_max, dict) else 192
                    if min_h > max_h_ref:
                        min_h = max_h_ref
                
                vars_h = []
                for d in dias_m:
                    td = "Finde_Feriado" if _is_finde(d, offset_dia, feriados) else "Semana"
                    for t in demanda_turnos.get(td, {}).keys():
                        if (emp.nombre, d, t) in turnos_vars:
                            h_turno = turnos_dict[t].horas if t in turnos_dict else 6
                            vars_h.append(turnos_vars[(emp.nombre, d, t)] * h_turno)
                
                dias_lic = [d for d in dias_m if d in emp.dias_licencia]
                # --- NUEVA LÓGICA DE CRÉDITO POR LICENCIA ---
                p_cred = _re.resolver_parametros_regla('CREDITO_HORARIO_LICENCIA', emp.nombre, ref_date, reglas_servicio, emp.reglas, ajustes_reglas)
                if _re.regla_existe(p_cred):
                    h_sem = p_cred.get('horas_por_semana', 36)
                    horas_lic = int((h_sem / 7.0) * len(dias_lic) + 0.5)
                else:
                    # Fallback proporcional (Enfermería)
                    horas_lic = int((float(min_h) / dias_del_bloque) * len(dias_lic) + 0.5)

                piso = int((min_h / dias_del_bloque) * len(dias_m) + 0.5)
                
                if vars_h:
                    modelo.Add(sum(vars_h) + horas_lic >= piso)
