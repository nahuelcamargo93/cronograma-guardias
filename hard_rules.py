from datetime import date, timedelta
from typing import List, Dict, Any, Set
import math
import rule_engine as _re
from models import Empleado, Turno
from utils import time_to_float
from data import FECHA_INICIO, FECHA_FIN, DEBUG_LOGS, DEBUG_DISABLE_MAX_HORAS, DIA_DEL_PADRE, DIA_DE_LA_MADRE
try:
    from data import EVITAR_MEZCLA_SEMANAL_DURA, ROTACION_MENSUAL_DURA
except ImportError:
    EVITAR_MEZCLA_SEMANAL_DURA = True
    ROTACION_MENSUAL_DURA = True


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

    # 1. Crear y vincular variables semanales (categorizando historial)
    vars_turno_sem = _crear_y_vincular_variables_semanales(
        modelo, turnos_vars, empleados, dias_del_bloque, fecha_inicio_dt, historial_semana_previa, offset_dia
    )

    _aplicar_licencias(modelo, turnos_vars, empleados, demanda_turnos, offset_dia, feriados)
    _aplicar_franco_forzado(modelo, turnos_vars, empleados, dias_del_bloque, fecha_inicio_dt, demanda_turnos, reglas_servicio, ajustes_reglas_personal)
    _aplicar_max_turnos(modelo, turnos_vars, empleados, semanas_calendario, reglas_servicio, ajustes_reglas_personal, historial_semana_previa, dias_del_bloque, fecha_inicio_dt)
    _aplicar_excluir_turnos(modelo, turnos_vars, empleados, dias_del_bloque, offset_dia, fecha_inicio_dt, reglas_servicio, ajustes_reglas_personal)
    _aplicar_min_turnos(modelo, turnos_vars, empleados, semanas_calendario, reglas_servicio, ajustes_reglas_personal, historial_semana_previa)
    _aplicar_cobertura_dinamica(modelo, turnos_vars, empleados, demanda_req, ajustes_demanda, dias_del_bloque, feriados, offset_dia, turnos_dict, fecha_inicio_dt, historial_semana_previa, reglas_servicio, ajustes_reglas_personal)
    _aplicar_limite_horas_semanales(modelo, turnos_vars, empleados, semanas_calendario, reglas_servicio, ajustes_reglas_personal, historial_semana_previa, demanda_turnos, turnos_dict, offset_dia, feriados, limite_horas_global)
    _aplicar_descanso_entre_turnos(modelo, turnos_vars, empleados, dias_del_bloque, fecha_inicio_dt, reglas_servicio, ajustes_reglas_personal, offset_dia, feriados, demanda_turnos, turnos_dict, historial_semana_previa)
    _aplicar_min_findes_mes(modelo, turnos_vars, empleados, demanda_turnos, offset_dia, feriados, reglas_servicio, ajustes_reglas_personal, dias_del_bloque, servicio_id)
    _aplicar_exacto_dia_especifico_mes_hard(modelo, turnos_vars, empleados, demanda_turnos, offset_dia, feriados, reglas_servicio, ajustes_reglas_personal, dias_del_bloque, turnos_dict)
    _aplicar_exacto_finde_y_dia(modelo, turnos_vars, empleados, demanda_turnos, offset_dia, feriados, reglas_servicio, ajustes_reglas_personal, dias_del_bloque, turnos_dict, modo_filtro="HARD")
    _aplicar_findes_completos_y_medios(modelo, turnos_vars, empleados, demanda_turnos, offset_dia, feriados, reglas_servicio, ajustes_reglas_personal, dias_del_bloque)
    _aplicar_un_solo_turno_por_dia(modelo, turnos_vars, empleados, dias_del_bloque, offset_dia, feriados, fecha_inicio_dt, demanda_turnos, reglas_servicio, ajustes_reglas_personal)
    _aplicar_patron_ciclico(modelo, turnos_vars, empleados, dias_del_bloque, fecha_inicio_dt, demanda_turnos, reglas_servicio, ajustes_reglas_personal, historial_semana_previa)
    _aplicar_max_horas_mes_calendario(modelo, turnos_vars, empleados, dias_del_bloque, offset_dia, feriados, fecha_inicio_dt, demanda_turnos, turnos_dict, reglas_servicio, ajustes_reglas_personal)
    _aplicar_fin_licencia(modelo, turnos_vars, empleados, dias_del_bloque, offset_dia, feriados, demanda_turnos, reglas_servicio, ajustes_reglas_personal, fecha_inicio_dt)
    _aplicar_min_horas_mes_calendario(modelo, turnos_vars, empleados, dias_del_bloque, offset_dia, feriados, fecha_inicio_dt, demanda_turnos, turnos_dict, reglas_servicio, ajustes_reglas_personal)
    _aplicar_reglas_fechas_especiales(modelo, turnos_vars, empleados, dias_del_bloque, fecha_inicio_dt, demanda_turnos, reglas_servicio, ajustes_reglas_personal)
    _aplicar_balance_dia_noche(modelo, turnos_vars, empleados, dias_del_bloque, offset_dia, feriados, demanda_turnos, turnos_dict, reglas_servicio, ajustes_reglas_personal, fecha_inicio_dt)
    _aplicar_personal_asociado(modelo, turnos_vars, empleados, dias_del_bloque, offset_dia, feriados, demanda_turnos, turnos_dict, reglas_servicio, ajustes_reglas_personal)
    _aplicar_max_dias_continuos(modelo, turnos_vars, empleados, dias_del_bloque, fecha_inicio_dt, offset_dia, feriados, demanda_turnos, turnos_dict, reglas_servicio, ajustes_reglas_personal, historial_semana_previa)

    # Aplicar mezcla semanal dura
    if EVITAR_MEZCLA_SEMANAL_DURA:
        _aplicar_evitar_mezcla_semanal_dura(modelo, vars_turno_sem, empleados, dias_del_bloque, fecha_inicio_dt)

    # Aplicar rotación mensual dura
    if ROTACION_MENSUAL_DURA:
        _aplicar_rotacion_mensual_dura(modelo, vars_turno_sem, empleados, dias_del_bloque, fecha_inicio_dt, reglas_servicio, ajustes_reglas_personal or {})

    return vars_turno_sem


def _aplicar_balance_dia_noche(modelo, turnos_vars, empleados, dias_del_bloque, offset_dia, feriados, demanda_turnos, turnos_dict, reglas_servicio, ajustes_reglas, fecha_inicio_dt):
    from data import FECHA_INICIO
    p_regla = _re.resolver_parametros_regla('MAX_NOCHE_VS_DIA', 'GLOBAL', FECHA_INICIO, reglas_servicio, {}, {})
    if not _re.regla_existe(p_regla) or _re.regla_suspendida(p_regla):
        return

    for d in range(dias_del_bloque):
        td = "Finde_Feriado" if _is_finde(d, offset_dia, feriados) else "Semana"
        lista_turnos = demanda_turnos.get(td, {}).keys()
        
        vars_dia = []
        vars_noche = []
        
        for t in lista_turnos:
            if t not in turnos_dict: continue
            hi = time_to_float(turnos_dict[t].hora_inicio)
            horas = turnos_dict[t].horas
            
            # Ignoramos guardias de 24hs para el balance (ya que cubren ambos)
            if horas >= 20:
                continue
                
            es_noche = hi >= 18.0 or hi < 5.0
            
            for emp in empleados:
                if (emp.nombre, d, t) in turnos_vars:
                    if es_noche:
                        vars_noche.append(turnos_vars[(emp.nombre, d, t)])
                    else:
                        vars_dia.append(turnos_vars[(emp.nombre, d, t)])
                        
        if vars_noche:
            # Si no hay variables de día (ej. nadie asignado al día), la noche debe ser 0.
            # sum(vars_noche) <= sum(vars_dia) lo cubre perfectamente.
            if vars_dia:
                modelo.Add(sum(vars_noche) <= sum(vars_dia))
            else:
                modelo.Add(sum(vars_noche) == 0)

def _aplicar_licencias(modelo, turnos_vars, empleados: List[Empleado], demanda_turnos, offset_dia, feriados):
    for emp in empleados:
        for d in emp.dias_licencia:
            for td in ["Semana", "Finde_Feriado"]:
                for t in demanda_turnos.get(td, {}).keys():
                    if (emp.nombre, d, t) in turnos_vars:
                        modelo.Add(turnos_vars[(emp.nombre, d, t)] == 0)

def _aplicar_max_turnos(modelo, turnos_vars, empleados, semanas_calendario, reglas_servicio, ajustes_reglas, historial, dias_del_bloque, fecha_inicio_dt):
    for emp in empleados:
        hist_emp = historial.get(emp.nombre, []) if historial else []
        
        # Primero evaluamos la restricción por mes calendario (si existe)
        meses = {}
        for d in range(dias_del_bloque):
            m_key = (fecha_inicio_dt + timedelta(days=d)).strftime("%Y-%m")
            meses.setdefault(m_key, []).append(d)

        for m_key, dias_m in meses.items():
            ref_date = (fecha_inicio_dt + timedelta(days=dias_m[0])).isoformat()
            params = _re.resolver_parametros_regla('MAX_TURNOS', emp.nombre, ref_date, reglas_servicio, emp.reglas, ajustes_reglas)
            if not _re.regla_existe(params) or not isinstance(params, list):
                continue
            
            for rest in params:
                max_mes = rest.get('max_por_mes')
                if max_mes is None: continue
                
                # Soporte para lista de turnos o turno único (retrocompatibilidad)
                t_tipos = rest.get('turnos')
                if not t_tipos and rest.get('turno'):
                    t_tipos = [rest.get('turno')]
                if not t_tipos: continue
                
                v_tipos_mes = []
                for t_tipo in t_tipos:
                    for d in dias_m:
                        if (emp.nombre, d, t_tipo) in turnos_vars:
                            v_tipos_mes.append(turnos_vars[(emp.nombre, d, t_tipo)])
                            
                if v_tipos_mes:
                    modelo.Add(sum(v_tipos_mes) <= max_mes)

        # Segundo evaluamos la restricción por bloque semanal (si existe)
        for (iso_year, iso_week), days in semanas_calendario.items():
            first_day_of_week = days[0][1]
            fecha_lunes = (first_day_of_week - timedelta(days=first_day_of_week.isocalendar()[2] - 1)).isoformat()
            
            params = _re.resolver_parametros_regla('MAX_TURNOS', emp.nombre, fecha_lunes, reglas_servicio, emp.reglas, ajustes_reglas)
            if not _re.regla_existe(params) or not isinstance(params, list):
                continue

            prev_en_sem = [h for h in hist_emp if date.fromisoformat(h['fecha']).isocalendar()[:2] == (iso_year, iso_week)]
            for rest in params:
                max_sem = rest.get('max_por_semana')
                if max_sem is None: continue
                
                t_tipos = rest.get('turnos')
                if not t_tipos and rest.get('turno'):
                    t_tipos = [rest.get('turno')]
                if not t_tipos: continue
                
                prev_tipo = sum(1 for h in prev_en_sem if h['turno'] in t_tipos)
                v_tipos_sem = []
                for t_tipo in t_tipos:
                    for d, fd in days:
                        if (emp.nombre, d, t_tipo) in turnos_vars:
                            v_tipos_sem.append(turnos_vars[(emp.nombre, d, t_tipo)])
                            
                if v_tipos_sem or prev_tipo > 0:
                    modelo.Add(sum(v_tipos_sem) + prev_tipo <= max_sem)

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

def _aplicar_cobertura_dinamica(modelo, turnos_vars, empleados, demanda_req, ajustes_demanda, dias_del_bloque, feriados, offset_dia, turnos_dict, fecha_inicio_dt, historial, reglas_servicio, ajustes_reglas):
    for dia in range(dias_del_bloque):
        es_f = _is_finde(dia, offset_dia, feriados)
        tipo_dia = "Finde_Feriado" if es_f else "Semana"
        fecha_actual_iso = (fecha_inicio_dt + timedelta(days=dia)).isoformat()
        dia_semana_actual = (dia + offset_dia) % 7
        
        # Agrupar demandas del día por puesto y ventana horaria (hora_inicio, hora_fin)
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
                
        # Para cada ventana de cada puesto, si hay específicas (con dias_semana), descartar las genéricas
        final_demandas = []
        for key, candidates in candidates_by_window.items():
            especificas = [c for c in candidates if c.get("dias_semana")]
            if especificas:
                final_demandas.extend(especificas)
            else:
                final_demandas.extend(candidates)
                
        # Agrupar demandas finales del día por ventana horaria (hora_inicio, hora_fin)
        demandas_por_ventana = {}
        for demanda in final_demandas:
            key = (demanda["hora_inicio"], demanda["hora_fin"])
            demandas_por_ventana.setdefault(key, []).append(demanda)
            
        for (h_start, h_end), window_demands in demandas_por_ventana.items():
            # Tiempos absolutos para esta ventana
            d_h_start = time_to_float(h_start)
            d_h_end = time_to_float(h_end)
            d_abs_start = dia * 24 + d_h_start
            if d_h_end <= d_h_start and not (d_h_start == 0 and d_h_end == 0):
                d_abs_end = (dia + 1) * 24 + d_h_end
            elif d_h_end == 0 and d_h_start > 0:
                d_abs_end = (dia + 1) * 24
            else:
                d_abs_end = dia * 24 + d_h_end
                
            # Identificar demandas específicas de esta ventana
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
                    
            # 1. Resolver y aplicar para Planta y Residente de forma combinada
            # Construir pools de variables que solapan con esta ventana
            pool_planta_normales = []
            pool_planta_extras = []
            extra_planta_vars_in_window = [] # Colecciona variables de personal extra (si aplica) en esta ventana
            
            pool_residente_normales = []
            pool_residente_extras = []
            
            has_planta_block_vars = False
            has_residente_block_vars = False
            
            for emp in empleados:
                # Verificar regla de extra para este empleado hoy
                fecha_bloque = (fecha_inicio_dt + timedelta(days=dia)).strftime("%Y-%m-%d")
                params_extra = _re.resolver_parametros_regla('PERSONAL_EXTRA_FUERA_MINIMO', emp.nombre, fecha_bloque, reglas_servicio, emp.reglas, ajustes_reglas)
                
                is_special_extra = False
                if _re.regla_existe(params_extra) and isinstance(params_extra, dict):
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
                                        ts_abs = -1 * 24 + time_to_float(t_info.hora_inicio)
                                        te_abs = ts_abs + t_info.horas
                                        if ts_abs <= d_abs_start + 0.01 and te_abs >= d_abs_end - 0.01:
                                            # NOTA: El personal especificado en la regla EXTRA se trata según su rol configurado.
                                            # Son tratados como normales, por lo que van a pool_planta_normales.
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
                            ts_abs = dia_t * 24 + time_to_float(t_info.hora_inicio)
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
                                    
            # Resolver límites para Planta
            if planta_dem:
                p_min = planta_dem.get("cantidad_min")
                p_max = planta_dem.get("cantidad_max")
                
                # Buscar ajustes de demanda Planta
                aj_p = None
                for (fi, ff), cambios in ajustes_demanda.items():
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
                        
                # Aplicar restricciones Planta
                if p_min is not None and p_min > 0:
                    if d_abs_end <= 8 and not has_planta_block_vars: pass
                    else: modelo.Add(sum(pool_planta_normales) >= p_min)
                if p_max is not None:
                    modelo.Add(sum(pool_planta_normales) <= p_max)
                    
            # Resolver límites para Residente
            if residente_dem:
                r_min = residente_dem.get("cantidad_min")
                r_max = residente_dem.get("cantidad_max")
                
                # Buscar ajustes de demanda Residente
                aj_r = None
                for (fi, ff), cambios in ajustes_demanda.items():
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
                        
                # Aplicar restricciones Residente con incremento dinámico por médicos de planta extra
                if r_min is not None and r_min > 0:
                    if d_abs_end <= 8 and not has_residente_block_vars: pass
                    else:
                        if extra_planta_vars_in_window:
                            for var in extra_planta_vars_in_window:
                                modelo.Add(sum(pool_residente_normales) >= r_min + var)
                        modelo.Add(sum(pool_residente_normales) >= r_min)
                if r_max is not None:
                    modelo.Add(sum(pool_residente_normales) <= r_max)
                    
            # 2. Manejar otras demandas normales (por compatibilidad si existen)
            for dem in otras_dems:
                c_min = dem.get("cantidad_min")
                c_max = dem.get("cantidad_max")
                
                aj_o = None
                for (fi, ff), cambios in ajustes_demanda.items():
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
                    params_extra = _re.resolver_parametros_regla('PERSONAL_EXTRA_FUERA_MINIMO', emp.nombre, fecha_bloque, reglas_servicio, emp.reglas, ajustes_reglas)
                    es_extra = False
                    if _re.regla_existe(params_extra) and isinstance(params_extra, dict):
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
                                            ts_abs = -1 * 24 + time_to_float(t_info.hora_inicio)
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
                                ts_abs = dia_t * 24 + time_to_float(t_info.hora_inicio)
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
                        if t not in turnos_dict:
                            raise ValueError(f"El turno '{t}' no está configurado en la base de datos (tabla turnos_config).")
                        h_turno = turnos_dict[t].horas
                        horas_semanales.append(turnos_vars[(emp.nombre, d, t)] * h_turno)
                        
            if horas_semanales or horas_previas > 0:
                params = _re.resolver_parametros_regla('MAX_HORAS_SEMANA', emp.nombre, fecha_lunes, reglas_servicio, emp.reglas, ajustes_reglas)
                if _re.regla_existe(params):
                    limite = params.get('limite', limite_global) if isinstance(params, dict) else limite_global
                    modelo.Add(sum(horas_semanales) + horas_previas <= limite)

def _aplicar_descanso_entre_turnos(modelo, turnos_vars, empleados, dias_del_bloque, fecha_inicio_dt, reglas_servicio, ajustes_reglas, offset_dia, feriados, demanda_turnos, turnos_dict, historial_semana_previa=None):
    # 1. Aplicar descanso por guardias del historial (mes/semana previa)
    if historial_semana_previa:
        for emp in empleados:
            hist_emp = historial_semana_previa.get(emp.nombre, [])
            for g in hist_emp:
                g_date = date.fromisoformat(g['fecha'])
                d_hist = (g_date - fecha_inicio_dt).days
                # Solo procesar guardias pasadas que ocurrieron antes de fecha_inicio_dt
                if d_hist >= 0:
                    continue
                
                params = _re.resolver_parametros_regla('DESCANSO_ENTRE_TURNOS', emp.nombre, g['fecha'], reglas_servicio, emp.reglas, ajustes_reglas)
                if not _re.regla_existe(params):
                    continue
                
                config_descanso = params.get('por_turno')
                min_descanso = None
                if config_descanso:
                    for k, v in config_descanso.items():
                        if k in g['turno']:
                            min_descanso = v
                            break
                if not min_descanso:
                    continue
                
                # Obtener o estimar hora_inicio y horas de la guardia histórica
                t1_name = g['turno']
                if t1_name in turnos_dict:
                    t1_info = turnos_dict[t1_name]
                    t1_start = time_to_float(t1_info.hora_inicio)
                    t1_hours = t1_info.horas
                else:
                    # Estimación heurística de hora_inicio basada en el nombre
                    if "Noche" in t1_name or "N_" in t1_name or "Noche_" in t1_name:
                        t1_start = 20.0
                    elif "Dia" in t1_name or "D_" in t1_name or "Mañana" in t1_name or "Tarde" in t1_name or "M_" in t1_name or "T_" in t1_name:
                        t1_start = 8.0
                    else:
                        t1_start = 8.0
                    t1_hours = g.get('horas') or 24
                
                t1_end_abs = d_hist * 24 + t1_start + t1_hours
                max_dias_futuro = math.ceil(min_descanso / 24) + 1
                
                # Evaluar el impacto en los días del bloque actual (d_fut >= 0)
                for d_fut in range(0, min(d_hist + max_dias_futuro, dias_del_bloque)):
                    td_fut = "Finde_Feriado" if _is_finde(d_fut, offset_dia, feriados) else "Semana"
                    turnos_man = [t for t in demanda_turnos.get(td_fut, {}).keys() if (emp.nombre, d_fut, t) in turnos_vars]
                    for t2 in turnos_man:
                        if t2 not in turnos_dict:
                            continue
                        t2_start_abs = d_fut * 24 + time_to_float(turnos_dict[t2].hora_inicio)
                        if t2_start_abs - t1_end_abs < min_descanso - 0.01:
                            modelo.Add(turnos_vars[(emp.nombre, d_fut, t2)] == 0)

    # 2. Aplicar descanso entre turnos dentro del bloque planificado
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
                    # Soporta tanto {"Dia": "Lunes"} como {"Fecha": "2026-06-15"}
                    fecha_asig = asig.get('Fecha')
                    dia_asig   = asig.get('Dia')
                    if (fecha_asig and fecha_asig == fecha_d) or (dia_asig and mapa_dias.get(dia_asig) == dia_semana):
                        fijos_hoy += 1
            
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
                            if t not in turnos_dict:
                                raise ValueError(f"El turno '{t}' no está configurado en la base de datos (tabla turnos_config).")
                            h_turno = turnos_dict[t].horas
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

def _aplicar_fin_licencia(modelo, turnos_vars, empleados, dias_del_bloque, offset_dia, feriados, demanda_turnos, reglas_servicio, ajustes_reglas, fecha_inicio_dt):
    # Solo aplicar si la regla existe en el catálogo del servicio y no está suspendida
    p_fin = _re.resolver_parametros_regla('FIN_LICENCIA', 'GLOBAL', FECHA_INICIO, reglas_servicio, {}, {})
    if not _re.regla_existe(p_fin) or _re.regla_suspendida(p_fin):
        return

    for emp in empleados:
        for d in range(dias_del_bloque - 1):
            if d in emp.dias_licencia and (d+1) not in emp.dias_licencia:
                # Si el profesional tiene un FRANCO_FORZADO el día siguiente, NO obligar a trabajar
                fecha_sig = (fecha_inicio_dt + timedelta(days=d+1)).isoformat()
                p_franco = _re.resolver_parametros_regla('FRANCO_FORZADO', emp.nombre, fecha_sig, reglas_servicio, emp.reglas, ajustes_reglas)
                if _re.regla_existe(p_franco) and not _re.regla_suspendida(p_franco):
                    continue

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
                            if t not in turnos_dict:
                                raise ValueError(f"El turno '{t}' no está configurado en la base de datos (tabla turnos_config).")
                            h_turno = turnos_dict[t].horas
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

                # Si el empleado no tiene ningún día laborable en este mes (ej. baja médica todo el mes),
                # vars_h estará vacío. En ese caso, solo aplicamos la restricción si el crédito por
                # licencia ya cubre el piso (caso trivialmente satisfecho). Si vars_h está vacío y el
                # crédito no alcanza a cubrir el piso, NO se aplica la restricción: sería matemáticamente
                # imposible exigir horas trabajadas a alguien que no tiene días disponibles.
                if vars_h:
                    # La restricción al solver es: horas_trabajadas + credito_licencia >= piso
                    # Solo tiene sentido si hay al menos un día laborable posible.
                    modelo.Add(sum(vars_h) + horas_lic >= piso)
                # Si vars_h está vacío y horas_lic < piso: el empleado está de licencia todo el mes,
                # no se añade ninguna restricción (no hay horas que pueda trabajar).

def _aplicar_min_findes_mes(modelo, turnos_vars, empleados, demanda_turnos, offset_dia, feriados, reglas_servicio, ajustes_reglas, dias_del_bloque, servicio_id=1, reglas_a_ignorar=None):
    fecha_inicio_dt = date.fromisoformat(FECHA_INICIO)
    for emp in empleados:
        # Resolver parámetros para MIN_FINDES_MES o EXACTO_FINDES_MES
        params_min = None
        if not reglas_a_ignorar or 'MIN_FINDES_MES' not in reglas_a_ignorar:
            params_min = _re.resolver_parametros_regla('MIN_FINDES_MES', emp.nombre, FECHA_INICIO, reglas_servicio, emp.reglas, ajustes_reglas)
            
        params_exacto = None
        if not reglas_a_ignorar or 'EXACTO_FINDES_MES' not in reglas_a_ignorar:
            params_exacto = _re.resolver_parametros_regla('EXACTO_FINDES_MES', emp.nombre, FECHA_INICIO, reglas_servicio, emp.reglas, ajustes_reglas)
            
        has_min = _re.regla_existe(params_min) and not _re.regla_suspendida(params_min)
        has_exacto = _re.regla_existe(params_exacto) and not _re.regla_suspendida(params_exacto)
        
        # Si MIN_FINDES_MES está suspendida para este empleado, heredamos la suspensión a EXACTO_FINDES_MES
        if has_exacto and params_min is not None and _re.regla_suspendida(params_min):
            has_exacto = False
            
        if not has_min and not has_exacto:
            continue
            
        is_exact = has_exacto
        params = params_exacto if has_exacto else params_min
        
        # Agrupar días por fin de semana (Sáb-Dom o Feriados)
        findes = {}
        for d in range(dias_del_bloque):
            fecha_d = fecha_inicio_dt + timedelta(days=d)
            if _is_finde(d, offset_dia, feriados):
                # Usar el lunes de la semana como clave para agrupar el finde
                lunes = (fecha_d - timedelta(days=fecha_d.weekday())).isoformat()
                findes.setdefault(lunes, []).append(d)
        
        # Calcular semanas disponibles (fines de semana donde el empleado no tiene licencia en TODOS los días)
        k = sum(1 for lunes, dias in findes.items() if any(d not in emp.dias_licencia for d in dias))
        
        if params.get('dinamico_licencias', False):
            # Regla de cálculo dinámico basada en licencias del mes
            if k >= 3:
                target_f = 2
            elif k >= 1:
                target_f = 1
            else:
                target_f = 0
        else:
            target_f = params.get('exacto_findes', params.get('min_findes', 1))
        
        vars_findes = []
        for lunes, dias in findes.items():
            # Un finde es trabajable si no tiene licencia ni FRANCO_FORZADO TODOS los días del finde
            dias_habilitados = []
            for d in dias:
                if d in emp.dias_licencia:
                    continue
                # Verificar si tiene franco forzado ese día
                fecha_d_str = (fecha_inicio_dt + timedelta(days=d)).isoformat()
                p_franco = _re.resolver_parametros_regla('FRANCO_FORZADO', emp.nombre, fecha_d_str, reglas_servicio, emp.reglas, ajustes_reglas)
                if _re.regla_existe(p_franco) and not _re.regla_suspendida(p_franco):
                    continue
                dias_habilitados.append(d)
            
            if not dias_habilitados:
                continue
            
            v_este_finde = modelo.NewBoolVar(f'traba_f_{emp.nombre}_{lunes}')
            pool_f = []
            for d in dias_habilitados:
                for td in ["Finde_Feriado"]:
                    for t in demanda_turnos.get(td, {}).keys():
                        if (emp.nombre, d, t) in turnos_vars:
                            pool_f.append(turnos_vars[(emp.nombre, d, t)])
            
            if pool_f:
                modelo.AddMaxEquality(v_este_finde, pool_f)
                vars_findes.append(v_este_finde)
        
        if vars_findes:
            # Relajar si el pedido es mayor a los findes disponibles
            target_real = min(target_f, len(vars_findes))
            if is_exact:
                modelo.Add(sum(vars_findes) == target_real)
            else:
                modelo.Add(sum(vars_findes) >= target_real)


def _aplicar_exacto_dia_especifico_mes_hard(modelo, turnos_vars, empleados, demanda_turnos, offset_dia, feriados, reglas_servicio, ajustes_reglas, dias_del_bloque, turnos_dict):
    """Restricción DURA: exactamente N veces un día específico de la semana en el mes.
    Versión hard de EXACTO_DIA_ESPECIFICO_MES. No puede ser violada por el solver.
    Registrar en la BD con código 'EXACTO_DIA_ESPECIFICO_MES_HARD'.
    JSON: {"dia_semana": "Viernes", "exacto_dias": 1, "dinamico_licencias": true}
    """
    from collections import defaultdict
    fecha_inicio_dt = date.fromisoformat(FECHA_INICIO)
    mapa_dias = {"lunes": 0, "martes": 1, "miercoles": 2, "jueves": 3, "viernes": 4, "sabado": 5, "domingo": 6}

    for emp in empleados:
        params = _re.resolver_parametros_regla(
            'EXACTO_DIA_ESPECIFICO_MES_HARD', emp.nombre, FECHA_INICIO,
            reglas_servicio, emp.reglas, ajustes_reglas
        )
        if not _re.regla_existe(params) or _re.regla_suspendida(params):
            continue

        dia_conf = params.get('dia_semana', 4)
        if isinstance(dia_conf, str):
            dia_str = dia_conf.lower()
            dia_str = dia_str.replace('é', 'e').replace('á', 'a').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
            dia_semana_target = mapa_dias.get(dia_str, 4)
        else:
            dia_semana_target = int(dia_conf)

        # Si el empleado tiene ASIGNACION_FIJA en algún día de la semana objetivo,
        # esa asignación ya controla cuántos veces trabaja ese día — no aplicar la restricción hard
        # para evitar doble restricción conflictiva.
        tiene_asig_fija_en_dia = False
        for d_check in range(dias_del_bloque):
            fecha_d_check = fecha_inicio_dt + timedelta(days=d_check)
            if fecha_d_check.weekday() != dia_semana_target:
                continue
            if d_check in emp.dias_licencia:
                continue
            fecha_check_str = fecha_d_check.isoformat()
            p_asig = _re.resolver_parametros_regla('ASIGNACION_FIJA', emp.nombre, fecha_check_str, reglas_servicio, emp.reglas, ajustes_reglas)
            if _re.regla_existe(p_asig) and not _re.regla_suspendida(p_asig):
                tiene_asig_fija_en_dia = True
                break
        if tiene_asig_fija_en_dia:
            continue  # La asignación fija ya determina cuántos viernes trabaja

        dia_conf = params.get('dia_semana', 4)
        if isinstance(dia_conf, str):
            dia_str = dia_conf.lower()
            dia_str = dia_str.replace('é', 'e').replace('á', 'a').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
            dia_semana_target = mapa_dias.get(dia_str, 4)
        else:
            dia_semana_target = int(dia_conf)

        exacto_dias = params.get('exacto_dias', 1)

        # Calcular target con dinamico_licencias (igual que soft y que EXACTO_FINDES_MES)
        if params.get('dinamico_licencias', False):
            # k = cantidad de semanas con al menos un día de finde disponible (sin licencia)
            finde_por_semana = defaultdict(list)
            for d_f in range(dias_del_bloque):
                if _is_finde(d_f, offset_dia, feriados):
                    fecha_df = fecha_inicio_dt + timedelta(days=d_f)
                    lunes_f = (fecha_df - timedelta(days=fecha_df.weekday())).isoformat()
                    finde_por_semana[lunes_f].append(d_f)

            k = sum(1 for dias_f in finde_por_semana.values() if any(d not in emp.dias_licencia for d in dias_f))

            if dia_semana_target == 4:  # Viernes
                if k == 5:
                    target_dias = 2
                elif k in (4, 2):
                    target_dias = 1
                else:
                    target_dias = 0
            else:
                target_dias = exacto_dias
        else:
            target_dias = exacto_dias

        if target_dias == 0:
            continue

        # Construir variables para cada ocurrencia del día en el mes (excluyendo licencias y francos)
        vars_dia = []
        for d in range(dias_del_bloque):
            fecha_d = fecha_inicio_dt + timedelta(days=d)
            if fecha_d.weekday() != dia_semana_target:
                continue
            if d in emp.dias_licencia:
                continue
            fecha_d_str = fecha_d.isoformat()
            p_franco = _re.resolver_parametros_regla('FRANCO_FORZADO', emp.nombre, fecha_d_str, reglas_servicio, emp.reglas, ajustes_reglas)
            if _re.regla_existe(p_franco) and not _re.regla_suspendida(p_franco):
                continue

            v_este_dia = modelo.NewBoolVar(f'traba_dia_esp_hard_{emp.nombre}_{dia_semana_target}_{d}')
            pool_d = []
            for t in turnos_dict.keys():
                if (emp.nombre, d, t) in turnos_vars:
                    pool_d.append(turnos_vars[(emp.nombre, d, t)])

            if pool_d:
                modelo.AddMaxEquality(v_este_dia, pool_d)
                vars_dia.append(v_este_dia)

        if vars_dia:
            target_real = min(target_dias, len(vars_dia))
            # RESTRICCION DURA: exactamente target_real días de ese día de la semana
            modelo.Add(sum(vars_dia) == target_real)


def _aplicar_findes_completos_y_medios(
    modelo,
    turnos_vars,
    empleados: List[Empleado],
    demanda_turnos: Dict,
    offset_dia: int,
    feriados: List[int],
    reglas_servicio: Dict[str, Any],
    ajustes_reglas: Dict[str, Any],
    dias_del_bloque: int
):
    fecha_inicio_dt = date.fromisoformat(FECHA_INICIO)
    for emp in empleados:
        params = _re.resolver_parametros_regla('FINDES_COMPLETOS_Y_MEDIOS', emp.nombre, FECHA_INICIO, reglas_servicio, emp.reglas, ajustes_reglas)
        if not _re.regla_existe(params) or _re.regla_suspendida(params):
            continue
            
        # Agrupar días por fin de semana (Sábado y Domingo)
        findes = {}
        for d in range(dias_del_bloque):
            fecha_d = fecha_inicio_dt + timedelta(days=d)
            wd = fecha_d.weekday()
            if wd in (5, 6): # 5: Saturday, 6: Sunday
                lunes = (fecha_d - timedelta(days=wd)).isoformat()
                findes.setdefault(lunes, []).append((d, wd))
                
        # Calcular semanas disponibles (fines de semana donde el empleado no tiene licencia en TODOS los días)
        # Y tampoco franco forzado en todos los días.
        k = 0
        for lunes, dias_info in findes.items():
            dias_disponibles = 0
            for d, wd in dias_info:
                if d in emp.dias_licencia:
                    continue
                # Verificar franco forzado
                fecha_d_str = (fecha_inicio_dt + timedelta(days=d)).isoformat()
                p_franco = _re.resolver_parametros_regla('FRANCO_FORZADO', emp.nombre, fecha_d_str, reglas_servicio, emp.reglas, ajustes_reglas)
                if _re.regla_existe(p_franco) and not _re.regla_suspendida(p_franco):
                    continue
                dias_disponibles += 1
            if dias_disponibles > 0:
                k += 1
                
        # Buscar configuración en base a k
        por_disp = params.get('por_disponibilidad', {})
        conf = por_disp.get(str(k))
        if not conf:
            # Fallbacks seguros
            if k >= 5:
                conf = {"completos": 3, "medios": 1}
            elif k == 4:
                conf = {"completos": 2, "medios": 1}
            elif k == 3:
                conf = {"completos": 1, "medios": 1}
            elif k == 2:
                conf = {"completos": 1, "medios": 0}
            elif k == 1:
                conf = {"completos": 0, "medios": 1}
            else:
                conf = {"completos": 0, "medios": 0}
                
        target_completos = conf.get('completos', 0)
        target_medios = conf.get('medios', 0)
        
        # Calcular los límites máximos posibles por licencias parciales
        findes_completos_posibles = 0
        findes_medios_posibles = 0
        
        vars_completo = []
        vars_medio = []
        
        for lunes, dias_info in findes.items():
            # Solo procesar fines de semana donde tanto sábado como domingo estén en el bloque
            d_sat = None
            d_sun = None
            for d, wd in dias_info:
                if wd == 5: d_sat = d
                elif wd == 6: d_sun = d
                
            if d_sat is None or d_sun is None:
                continue
                
            # Verificar si sábado y domingo están disponibles de licencia y franco forzado
            sat_disponible = d_sat not in emp.dias_licencia
            if sat_disponible:
                fecha_sat_str = (fecha_inicio_dt + timedelta(days=d_sat)).isoformat()
                p_franco_sat = _re.resolver_parametros_regla('FRANCO_FORZADO', emp.nombre, fecha_sat_str, reglas_servicio, emp.reglas, ajustes_reglas)
                if _re.regla_existe(p_franco_sat) and not _re.regla_suspendida(p_franco_sat):
                    sat_disponible = False
                    
            sun_disponible = d_sun not in emp.dias_licencia
            if sun_disponible:
                fecha_sun_str = (fecha_inicio_dt + timedelta(days=d_sun)).isoformat()
                p_franco_sun = _re.resolver_parametros_regla('FRANCO_FORZADO', emp.nombre, fecha_sun_str, reglas_servicio, emp.reglas, ajustes_reglas)
                if _re.regla_existe(p_franco_sun) and not _re.regla_suspendida(p_franco_sun):
                    sun_disponible = False
                    
            if sat_disponible and sun_disponible:
                findes_completos_posibles += 1
            if sat_disponible or sun_disponible:
                findes_medios_posibles += 1
                
            # Variable: Trabaja sábado
            pool_sat = [turnos_vars[(emp.nombre, d_sat, t)] for t in demanda_turnos.get("Finde_Feriado", {}).keys() if (emp.nombre, d_sat, t) in turnos_vars]
            v_sabado = modelo.NewBoolVar(f'traba_sat_{emp.nombre}_{lunes}')
            if pool_sat:
                modelo.AddMaxEquality(v_sabado, pool_sat)
            else:
                modelo.Add(v_sabado == 0)
                
            # Variable: Trabaja domingo
            pool_sun = [turnos_vars[(emp.nombre, d_sun, t)] for t in demanda_turnos.get("Finde_Feriado", {}).keys() if (emp.nombre, d_sun, t) in turnos_vars]
            v_domingo = modelo.NewBoolVar(f'traba_dom_{emp.nombre}_{lunes}')
            if pool_sun:
                modelo.AddMaxEquality(v_domingo, pool_sun)
            else:
                modelo.Add(v_domingo == 0)
                
            # Variable: Finde completo (Trabaja sábado AND trabaja domingo)
            v_completo = modelo.NewBoolVar(f'f_completo_{emp.nombre}_{lunes}')
            modelo.AddMinEquality(v_completo, [v_sabado, v_domingo])
            vars_completo.append(v_completo)
            
            # Variable: Finde medio (Trabaja exactamente uno)
            v_medio = modelo.NewBoolVar(f'f_medio_{emp.nombre}_{lunes}')
            modelo.Add(v_sabado + v_domingo - 2 * v_completo == v_medio)
            vars_medio.append(v_medio)
            
        # Acotar los objetivos según las limitaciones reales de este profesional
        target_completos_real = min(target_completos, findes_completos_posibles)
        # La suma de completos y medios no puede superar el total de fines de semana donde al menos un día es trabajable
        target_medios_real = min(target_medios, findes_medios_posibles - target_completos_real)
        
        if vars_completo:
            modelo.Add(sum(vars_completo) == target_completos_real)
        if vars_medio:
            modelo.Add(sum(vars_medio) == target_medios_real)


def _aplicar_reglas_fechas_especiales(modelo, turnos_vars, empleados, dias_del_bloque, fecha_inicio_dt, demanda_turnos, reglas_servicio, ajustes_reglas):
    for emp in empleados:
        for d in range(dias_del_bloque):
            fecha_d_dt = fecha_inicio_dt + timedelta(days=d)
            fecha_d_str = fecha_d_dt.isoformat()
            
            # 1. CUMPLEAÑOS
            params_cumple = _re.resolver_parametros_regla('CUMPLEANOS_LIBRE', emp.nombre, fecha_d_str, reglas_servicio, emp.reglas, ajustes_reglas)
            if _re.regla_existe(params_cumple) and not _re.regla_suspendida(params_cumple):
                if emp.fecha_cumpleanos and isinstance(emp.fecha_cumpleanos, str):
                    # El formato en la BD puede ser YYYY-MM-DD o MM-DD. Intentamos ambos.
                    match = False
                    try:
                        f_cumple = date.fromisoformat(emp.fecha_cumpleanos)
                        if f_cumple.month == fecha_d_dt.month and f_cumple.day == fecha_d_dt.day:
                            match = True
                    except ValueError:
                        # Probar si es MM-DD
                        if len(emp.fecha_cumpleanos) == 5 and emp.fecha_cumpleanos[2] == '-':
                            if emp.fecha_cumpleanos == f"{fecha_d_dt.month:02d}-{fecha_d_dt.day:02d}":
                                match = True
                    
                    if match:
                        _prohibir_turnos_dia(modelo, turnos_vars, emp.nombre, d, demanda_turnos)

            # 2. DIA DEL PADRE / MADRE
            params_familia = _re.resolver_parametros_regla('DIA_MADRE_PADRE_LIBRE', emp.nombre, fecha_d_str, reglas_servicio, emp.reglas, ajustes_reglas)
            if _re.regla_existe(params_familia) and not _re.regla_suspendida(params_familia):
                # Dia del Padre
                if emp.es_padre and fecha_d_str == DIA_DEL_PADRE:
                    _prohibir_turnos_dia(modelo, turnos_vars, emp.nombre, d, demanda_turnos)
                
                # Dia de la Madre
                if emp.es_madre and fecha_d_str == DIA_DE_LA_MADRE:
                    _prohibir_turnos_dia(modelo, turnos_vars, emp.nombre, d, demanda_turnos)

def _aplicar_franco_forzado(modelo, turnos_vars, empleados, dias_del_bloque, fecha_inicio_dt, demanda_turnos, reglas_servicio, ajustes_reglas):
    """
    Aplica la regla FRANCO_FORZADO: prohíbe todos los turnos de una persona
    en una fecha o rango de fechas concreto.

    Se configura exclusivamente via personal_reglas_ajustes:
      - codigo_regla : FRANCO_FORZADO
      - accion       : SOBRESCRIBIR
      - fecha_inicio : primer día del franco (ej. '2026-06-10')
      - fecha_fin    : último día del franco  (ej. '2026-06-10' para un solo día)
      - parametros_json: {} (no necesita parámetros adicionales)

    A diferencia de las licencias (LPP/LAR), el FRANCO_FORZADO:
      - No afecta al contador de horas (no genera crédito horario).
      - Es gestionable desde la UI sin tocar la tabla licencias.
      - Puede suspenderse/sobreescribirse con la jerarquía normal del rule_engine.
    """
    for emp in empleados:
        for d in range(dias_del_bloque):
            if d in emp.dias_licencia:
                continue  # Ya bloqueado por licencia formal, no hace falta duplicar
            fecha_d_str = (fecha_inicio_dt + timedelta(days=d)).isoformat()
            params = _re.resolver_parametros_regla(
                'FRANCO_FORZADO', emp.nombre, fecha_d_str,
                reglas_servicio, emp.reglas, ajustes_reglas
            )
            if _re.regla_existe(params) and not _re.regla_suspendida(params):
                _prohibir_turnos_dia(modelo, turnos_vars, emp.nombre, d, demanda_turnos)

def _prohibir_turnos_dia(modelo, turnos_vars, nombre_emp, dia_idx, demanda_turnos):
    for td in ["Semana", "Finde_Feriado"]:
        for t in demanda_turnos.get(td, {}).keys():
            if (nombre_emp, dia_idx, t) in turnos_vars:
                modelo.Add(turnos_vars[(nombre_emp, dia_idx, t)] == 0)

def _aplicar_patron_ciclico(modelo, turnos_vars, empleados, dias_del_bloque, fecha_inicio_dt, demanda_turnos, reglas_servicio, ajustes_reglas, historial):
    for emp in empleados:
        # Resolver parametros de la regla (ej: {"trabajo": 10, "franco": 4})
        params = _re.resolver_parametros_regla('PATRON_CICLICO', emp.nombre, fecha_inicio_dt.isoformat(), reglas_servicio, emp.reglas, ajustes_reglas)
        if not _re.regla_existe(params) or _re.regla_suspendida(params):
            continue
            
        # Extraer X y Y
        if not isinstance(params, dict): continue
        X = params.get('trabajo')
        Y = params.get('franco')
        if not X or not Y or X <= 0 or Y <= 0: continue
        
        L = X + Y
        
        # 1. Crear las variables booleanas para los L posibles offsets
        offset_vars = {}
        for o in range(L):
            offset_vars[o] = modelo.NewBoolVar(f'offset_{emp.nombre}_{o}')
            
        # Exactamente un offset debe ser elegido
        modelo.Add(sum(offset_vars.values()) == 1)
        
        # 2. Analizar el historial para forzar/limitar el offset y dar continuidad
        hist_emp = historial.get(emp.nombre, []) if historial else []
        if hist_emp:
            # Reconstruir H[d] para d en [-L, -1]
            worked_days = {}
            for h in hist_emp:
                h_date = date.fromisoformat(h['fecha'])
                delta_days = (h_date - fecha_inicio_dt).days
                if -L <= delta_days <= -1:
                    worked_days[delta_days] = True
            
            # Solo si hay algo en el historial reciente intentamos matchear
            if worked_days:
                offset_conflicts = {}
                for o in range(L):
                    conflicts = 0
                    for d in range(-L, 0):
                        predicted = 1 if (d + o) % L < X else 0
                        actual = 1 if worked_days.get(d, False) else 0
                        if predicted != actual:
                            conflicts += 1
                    offset_conflicts[o] = conflicts
                
                min_conflicts = min(offset_conflicts.values())
                # Forzar al solver a elegir solo entre los offsets con el minimo de conflictos
                for o in range(L):
                    if offset_conflicts[o] > min_conflicts:
                        modelo.Add(offset_vars[o] == 0)
        
        # 3. Aplicar el patron al bloque de dias a planificar
        for d in range(dias_del_bloque):
            turnos_hoy = [var for (nombre, dia, t), var in turnos_vars.items() if nombre == emp.nombre and dia == d]
            
            if not turnos_hoy:
                continue
            
            # Si hay licencia o franco forzado, omitimos forzar el trabajo ese dia
            # para no generar Infeasibility (la rueda del ciclo sigue girando igual)
            if d in emp.dias_licencia:
                continue
            
            fecha_d_str = (fecha_inicio_dt + timedelta(days=d)).isoformat()
            p_franco = _re.resolver_parametros_regla('FRANCO_FORZADO', emp.nombre, fecha_d_str, reglas_servicio, emp.reglas, ajustes_reglas)
            if _re.regla_existe(p_franco) and not _re.regla_suspendida(p_franco):
                continue

            # Forzar W_d = 1 si es dia de trabajo en la plantilla, o 0 si es franco
            rhs_terms = []
            for o in range(L):
                ideal = 1 if (d + o) % L < X else 0
                if ideal == 1:
                    rhs_terms.append(offset_vars[o])
                    
            modelo.Add(sum(turnos_hoy) == sum(rhs_terms))


def _aplicar_personal_asociado(
    modelo,
    turnos_vars,
    empleados: List[Empleado],
    dias_del_bloque: int,
    offset_dia: int,
    feriados: List[int],
    demanda_turnos: Dict,
    turnos_dict: Dict[str, Turno],
    reglas_servicio: Dict[str, Any],
    ajustes_reglas: Dict[str, Any]
):
    """
    Regla dura: Los miembros de las parejas asociadas deben coincidir exactamente
    en sus franjas horarias de trabajo (hora_inicio, hora_fin) y francos
    en todo momento del cronograma.
    """
    params = _re.resolver_parametros_regla(
        'PERSONAL_ASOCIADO', 'GLOBAL', FECHA_INICIO,
        reglas_servicio, {}, {}
    )
    if not _re.regla_existe(params) or _re.regla_suspendida(params):
        return

    parejas = params.get('parejas', [])
    for p1_name, p2_name in parejas:
        # Verificar que ambos empleados existan en el bloque
        emp_names = {e.nombre for e in empleados}
        if p1_name not in emp_names or p2_name not in emp_names:
            if DEBUG_LOGS:
                print(f"[WARNING] Regla PERSONAL_ASOCIADO: Uno o ambos de {p1_name} y {p2_name} no están en este bloque.")
            continue
            
        for d in range(dias_del_bloque):
            td = "Finde_Feriado" if _is_finde(d, offset_dia, feriados) else "Semana"
            lista_turnos = demanda_turnos.get(td, {}).keys()
            
            # Agrupar los turnos activos de este día por su franja horaria (hora_inicio, horas)
            franjas = {}
            for t in lista_turnos:
                t_info = turnos_dict.get(t)
                if t_info:
                    key = (t_info.hora_inicio, t_info.horas)
                    franjas.setdefault(key, []).append(t)
            
            for key, turnos_franja in franjas.items():
                vars1 = [turnos_vars[(p1_name, d, t)] for t in turnos_franja if (p1_name, d, t) in turnos_vars]
                vars2 = [turnos_vars[(p2_name, d, t)] for t in turnos_franja if (p2_name, d, t) in turnos_vars]
                
                # Obligar a que la asignación en la franja horaria coincida exactamente.
                # Como cada persona puede trabajar a lo sumo 1 turno al día, sum(vars) será 0 o 1.
                modelo.Add(sum(vars1) == sum(vars2))


def mapear_turno_a_familias(turno: str) -> List[str]:
    """
    Mapea el nombre de un turno a las familias correspondientes (M, T, TN, N).
    Retorna una lista de familias.
    """
    t = turno.upper()
    
    # Mapeo exacto
    if t == 'M':
        return ['M']
    if t == 'T':
        return ['T']
    if t == 'TN':
        return ['TN']
    if t == 'N' or t == 'NOCHE':
        return ['N']
        
    # Mapeos combinados/especiales
    if 'MT' in t or 'MAÑANA' in t or 'MAANA' in t:
        if 'TARDE' in t:
            return ['M', 'T']
        return ['M']
    if 'TNN' in t:
        return ['TN', 'N']
    if 'TARDE' in t:
        return ['T']
    if 'UCO' in t or 'UTI' in t:
        if t.startswith('M'):
            return ['M']
        if t.startswith('T'):
            return ['T']
            
    # Fallback/General
    familias = []
    if 'M' in t:
        familias.append('M')
    if 'T' in t:
        if 'TN' not in t or t.count('T') > 1:
            familias.append('T')
    if 'TN' in t:
        familias.append('TN')
    if 'N' in t:
        if 'TN' not in t or t.count('N') > 1:
            familias.append('N')
            
    return familias if familias else ['M']


def _determinar_familia_ganadora_historial(historial_semana, lunes_semana_dt):
    # Contamos la cantidad de apariciones de cada familia
    conteos = {'M': 0, 'T': 0, 'TN': 0, 'N': 0}
    # Para desempatar, registramos la fecha del último turno asignado a cada familia
    ultimo_registro = {'M': date.min, 'T': date.min, 'TN': date.min, 'N': date.min}
    
    tiene_historial = False
    for h_guardia in historial_semana:
        h_fecha_str = h_guardia.get('fecha')
        if not h_fecha_str:
            continue
        h_fecha = date.fromisoformat(h_fecha_str)
        # Verificar si la guardia pertenece a esta semana calendario
        if lunes_semana_dt <= h_fecha < lunes_semana_dt + timedelta(days=7):
            h_t = h_guardia.get('turno', '')
            familias = mapear_turno_a_familias(h_t)
            for f in familias:
                if f in conteos:
                    conteos[f] += 1
                    tiene_historial = True
                    if h_fecha > ultimo_registro[f]:
                        ultimo_registro[f] = h_fecha
                        
    if not tiene_historial:
        return None
        
    # Encontrar el máximo de conteos
    max_cant = max(conteos.values())
    candidatos = [f for f, c in conteos.items() if c == max_cant]
    
    if len(candidatos) == 1:
        return candidatos[0]
        
    # En caso de empate, elegir el que haya sucedido último en el tiempo
    # (desempate por fecha más reciente)
    ganador = candidatos[0]
    max_fecha = ultimo_registro[ganador]
    for c in candidatos[1:]:
        if ultimo_registro[c] > max_fecha:
            max_fecha = ultimo_registro[c]
            ganador = c
            
    return ganador


def _crear_y_vincular_variables_semanales(
    modelo,
    turnos_vars,
    empleados: List[Empleado],
    dias_del_bloque: int,
    fecha_inicio_dt: date,
    historial_semana_previa: Dict[str, List[Dict]],
    offset_dia: int
) -> Dict[tuple, Dict[str, Any]]:
    # 1. Agrupar dias por semana calendario (Lunes-Domingo)
    dias_por_semana_calendario = {}
    for d in range(dias_del_bloque):
        fecha_d = fecha_inicio_dt + timedelta(days=d)
        lunes_semana = fecha_d - timedelta(days=fecha_d.weekday())
        sem_key = lunes_semana.isoformat()
        dias_por_semana_calendario.setdefault(sem_key, []).append(d)

    vars_turno_sem = {}

    for emp in empleados:
        nombre = emp.nombre
        hist_prev = historial_semana_previa.get(nombre, []) if historial_semana_previa else []

        for sem_key, dias_semana_actual in dias_por_semana_calendario.items():
            sem_id = sem_key.replace("-", "_")
            lunes_semana_dt = date.fromisoformat(sem_key)

            is_M = modelo.NewBoolVar(f'is_M_{nombre}_{sem_id}')
            is_T = modelo.NewBoolVar(f'is_T_{nombre}_{sem_id}')
            is_TN = modelo.NewBoolVar(f'is_TN_{nombre}_{sem_id}')
            is_N = modelo.NewBoolVar(f'is_N_{nombre}_{sem_id}')

            vars_turno_sem[(nombre, sem_key)] = {
                'M': is_M,
                'T': is_T,
                'TN': is_TN,
                'N': is_N
            }

            # Vincular a las variables diarias de planificación activa
            for d in dias_semana_actual:
                if (nombre, d, 'M') in turnos_vars:
                    modelo.AddImplication(turnos_vars[(nombre, d, 'M')], is_M)
                if (nombre, d, 'T') in turnos_vars:
                    modelo.AddImplication(turnos_vars[(nombre, d, 'T')], is_T)
                if (nombre, d, 'TN') in turnos_vars:
                    modelo.AddImplication(turnos_vars[(nombre, d, 'TN')], is_TN)
                if (nombre, d, 'N') in turnos_vars:
                    modelo.AddImplication(turnos_vars[(nombre, d, 'N')], is_N)
                if (nombre, d, 'MT') in turnos_vars:
                    modelo.Add(is_M + is_T >= 1).OnlyEnforceIf(turnos_vars[(nombre, d, 'MT')])
                if (nombre, d, 'TNN') in turnos_vars:
                    modelo.Add(is_TN + is_N >= 1).OnlyEnforceIf(turnos_vars[(nombre, d, 'TNN')])

            # Vincular al historial (Categorización)
            hist_winner = _determinar_familia_ganadora_historial(hist_prev, lunes_semana_dt)

            if hist_winner:
                # Si hay historial categorizado, se fuerza esa familia a 1
                if hist_winner == 'M':
                    modelo.Add(is_M == 1)
                elif hist_winner == 'T':
                    modelo.Add(is_T == 1)
                elif hist_winner == 'TN':
                    modelo.Add(is_TN == 1)
                elif hist_winner == 'N':
                    modelo.Add(is_N == 1)

            # Acotación superior (upper bounds) para evitar trampas del solver durante licencias/francos
            vars_M_semana = [turnos_vars[(nombre, d, 'M')] for d in dias_semana_actual if (nombre, d, 'M') in turnos_vars]
            vars_T_semana = [turnos_vars[(nombre, d, 'T')] for d in dias_semana_actual if (nombre, d, 'T') in turnos_vars]
            vars_TN_semana = [turnos_vars[(nombre, d, 'TN')] for d in dias_semana_actual if (nombre, d, 'TN') in turnos_vars]
            vars_N_semana = [turnos_vars[(nombre, d, 'N')] for d in dias_semana_actual if (nombre, d, 'N') in turnos_vars]
            vars_MT_semana = [turnos_vars[(nombre, d, 'MT')] for d in dias_semana_actual if (nombre, d, 'MT') in turnos_vars]
            vars_TNN_semana = [turnos_vars[(nombre, d, 'TNN')] for d in dias_semana_actual if (nombre, d, 'TNN') in turnos_vars]

            hist_M = 1 if hist_winner == 'M' else 0
            hist_T = 1 if hist_winner == 'T' else 0
            hist_TN = 1 if hist_winner == 'TN' else 0
            hist_N = 1 if hist_winner == 'N' else 0

            modelo.Add(is_M <= sum(vars_M_semana) + sum(vars_MT_semana) + hist_M)
            modelo.Add(is_T <= sum(vars_T_semana) + sum(vars_MT_semana) + hist_T)
            modelo.Add(is_TN <= sum(vars_TN_semana) + sum(vars_TNN_semana) + hist_TN)
            modelo.Add(is_N <= sum(vars_N_semana) + sum(vars_TNN_semana) + hist_N)

    return vars_turno_sem


def _aplicar_evitar_mezcla_semanal_dura(
    modelo,
    vars_turno_sem: Dict[tuple, Dict[str, Any]],
    empleados: List[Empleado],
    dias_del_bloque: int,
    fecha_inicio_dt: date
):
    dias_por_semana_calendario = {}
    for d in range(dias_del_bloque):
        fecha_d = fecha_inicio_dt + timedelta(days=d)
        lunes_semana = fecha_d - timedelta(days=fecha_d.weekday())
        sem_key = lunes_semana.isoformat()
        dias_por_semana_calendario.setdefault(sem_key, []).append(d)

    for emp in empleados:
        nombre = emp.nombre
        for sem_key in dias_por_semana_calendario.keys():
            v_dict = vars_turno_sem.get((nombre, sem_key))
            if v_dict:
                is_M = v_dict['M']
                is_T = v_dict['T']
                is_TN = v_dict['TN']
                is_N = v_dict['N']
                modelo.Add(is_M + is_T + is_TN + is_N <= 1)


def _aplicar_rotacion_mensual_dura(
    modelo,
    vars_turno_sem: Dict[tuple, Dict[str, Any]],
    empleados: List[Empleado],
    dias_del_bloque: int,
    fecha_inicio_dt: date,
    reglas_servicio: Dict[str, Any],
    ajustes_personal: Dict[str, Any]
):
    dias_por_semana_calendario = {}
    for d in range(dias_del_bloque):
        fecha_d = fecha_inicio_dt + timedelta(days=d)
        lunes_semana = fecha_d - timedelta(days=fecha_d.weekday())
        sem_key = lunes_semana.isoformat()
        dias_por_semana_calendario.setdefault(sem_key, []).append(d)

    for emp in empleados:
        nombre = emp.nombre
        dias_bloqueados_persona = emp.dias_licencia
        
        semanas_M = []
        semanas_T = []
        semanas_TN = []
        semanas_N = []
        for sem_key in dias_por_semana_calendario.keys():
            v_dict = vars_turno_sem.get((nombre, sem_key))
            if v_dict:
                semanas_M.append(v_dict['M'])
                semanas_T.append(v_dict['T'])
                semanas_TN.append(v_dict['TN'])
                semanas_N.append(v_dict['N'])

        params_div = _re.resolver_parametros_regla('PENALIZACION_TURNO_AUSENTE', nombre, FECHA_INICIO, reglas_servicio, emp.reglas, ajustes_personal)
        if _re.regla_existe(params_div) and not _re.regla_suspendida(params_div):
            mapping_div = {'M': semanas_M, 'T': semanas_T, 'TN': semanas_TN, 'N': semanas_N}
            
            has_family = {}
            for t_code, sem_vars in mapping_div.items():
                if sem_vars:
                    has_f = modelo.NewBoolVar(f'has_family_hard_{t_code}_{nombre}')
                    modelo.Add(sum(sem_vars) >= 1).OnlyEnforceIf(has_f)
                    modelo.Add(sum(sem_vars) == 0).OnlyEnforceIf(has_f.Not())
                    has_family[t_code] = has_f
            
            semanas_disponibles = 0
            for sem_key_rot, dias_sem_rot in dias_por_semana_calendario.items():
                if len(dias_sem_rot) >= 4:
                    dias_libres_rot = [d for d in dias_sem_rot if d not in dias_bloqueados_persona]
                    if len(dias_libres_rot) >= 4:
                        semanas_disponibles += 1

            req_families = min(4, semanas_disponibles)

            if req_families > 0 and has_family:
                modelo.Add(sum(has_family.values()) >= req_families)


def _aplicar_max_dias_continuos(
    modelo,
    turnos_vars,
    empleados: List[Empleado],
    dias_del_bloque: int,
    fecha_inicio_dt: date,
    offset_dia: int,
    feriados: List[int],
    demanda_turnos: Dict,
    turnos_dict: Dict[str, Turno],
    reglas_servicio: Dict[str, Any],
    ajustes_reglas: Dict[str, Any],
    historial: Dict[str, List[Dict]]
):
    """
    Regla dura: Controla que un empleado no trabaje más de max_dias de forma consecutiva,
    teniendo en cuenta también el historial del mes/ciclo anterior.
    """
    for emp in empleados:
        ref_date = fecha_inicio_dt.isoformat()
        params = _re.resolver_parametros_regla(
            'MAX_DIAS_CONTINUOS', emp.nombre, ref_date,
            reglas_servicio, emp.reglas, ajustes_reglas
        )
        if not _re.regla_suspendida(params):
            max_dias = params.get('max_dias') if isinstance(params, dict) else None
            if max_dias is None or max_dias <= 0:
                continue

            traba_dia = {}
            for d in range(dias_del_bloque):
                td = "Finde_Feriado" if _is_finde(d, offset_dia, feriados) else "Semana"
                turnos_dia = [
                    turnos_vars[(emp.nombre, d, t)] for t in demanda_turnos.get(td, {}).keys()
                    if (emp.nombre, d, t) in turnos_vars
                ]
                if turnos_dia:
                    v_dia = modelo.NewBoolVar(f"traba_dia_{emp.nombre}_dia{d}")
                    modelo.Add(v_dia == sum(turnos_dia))
                    traba_dia[d] = v_dia
                else:
                    traba_dia[d] = 0

            hist_emp = historial.get(emp.nombre, []) if historial else []
            historical_worked_dates = {h['fecha'] for h in hist_emp}

            T = {}
            for d in range(-max_dias, dias_del_bloque):
                if d < 0:
                    fecha_h = (fecha_inicio_dt + timedelta(days=d)).strftime("%Y-%m-%d")
                    T[d] = 1 if fecha_h in historical_worked_dates else 0
                else:
                    T[d] = traba_dia[d]

            window_size = max_dias + 1
            for start in range(-max_dias, dias_del_bloque - max_dias):
                window_vars = [T[d] for d in range(start, start + window_size)]
                modelo.Add(sum(window_vars) <= max_dias)


def _aplicar_exacto_finde_y_dia(modelo, turnos_vars, empleados, demanda_turnos, offset_dia, feriados, reglas_servicio, ajustes_reglas, dias_del_bloque, turnos_dict, modo_filtro="HARD", penalizaciones_ad_hoc=None):
    from collections import defaultdict
    fecha_inicio_dt = date.fromisoformat(FECHA_INICIO)
    mapa_dias = {"lunes": 0, "martes": 1, "miercoles": 2, "jueves": 3, "viernes": 4, "sabado": 5, "domingo": 6}

    for emp in empleados:
        params = _re.resolver_parametros_regla(
            'EXACTO_FINDE_Y_DIA', emp.nombre, FECHA_INICIO,
            reglas_servicio, emp.reglas, ajustes_reglas
        )
        if not _re.regla_existe(params) or _re.regla_suspendida(params):
            continue

        # Leer modo y filtrar si no corresponde al modo_filtro actual
        modo = params.get('modo', 'HARD').upper()
        if modo != modo_filtro:
            continue

        peso_soft = params.get('peso_soft', 100000)

        # --- 1. CONFIGURACIÓN DÍA DE LA SEMANA ---
        dia_conf = params.get('dia_semana', 4)
        if isinstance(dia_conf, str):
            dia_str = dia_conf.lower().replace('é', 'e').replace('á', 'a').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
            dia_semana_target = mapa_dias.get(dia_str, 4)
          
        else:
            dia_semana_target = int(dia_conf)

        # --- 2. CÁLCULO DE DISPONIBILIDAD DE FINES DE SEMANA ---
        findes = {}
        for d in range(dias_del_bloque):
            fecha_d = fecha_inicio_dt + timedelta(days=d)
            if _is_finde(d, offset_dia, feriados):
                lunes = (fecha_d - timedelta(days=fecha_d.weekday())).isoformat()
                findes.setdefault(lunes, []).append(d)

        # k = cantidad de fines de semana donde el empleado no tiene licencia en TODOS los días
        k = sum(1 for lunes, dias in findes.items() if any(d not in emp.dias_licencia for d in dias))

        # --- 3. CÁLCULO DE DISPONIBILIDAD DEL DÍA ESPECÍFICO ---
        k_dia = 0
        for d in range(dias_del_bloque):
            fecha_d = fecha_inicio_dt + timedelta(days=d)
            if fecha_d.weekday() == dia_semana_target:
                if d in emp.dias_licencia:
                    continue
                fecha_d_str = fecha_d.isoformat()
                p_franco = _re.resolver_parametros_regla('FRANCO_FORZADO', emp.nombre, fecha_d_str, reglas_servicio, emp.reglas, ajustes_reglas)
                if _re.regla_existe(p_franco) and not _re.regla_suspendida(p_franco):
                    continue
                k_dia += 1

        # --- 4. OBTENER TARGETS ---
        # Target Fines de Semana
        mapping_findes = params.get('findes_por_disponibilidad')
        if mapping_findes and isinstance(mapping_findes, dict):
            target_findes = mapping_findes.get(str(k), mapping_findes.get(k, 0))
        else:
            # Fallback default
            if k >= 3:
                target_findes = 2
            elif k >= 1:
                target_findes = 1
            else:
                target_findes = 0

        # Target Días
        mapping_dias = params.get('dias_por_disponibilidad')
        if mapping_dias and isinstance(mapping_dias, dict):
            target_dias = mapping_dias.get(str(k_dia), mapping_dias.get(k_dia, 0))
        else:
            # Fallback default (para Viernes/otro día de la semana)
            if k_dia == 5:
                target_dias = 2
            elif k_dia in (4, 2):
                target_dias = 1
            else:
                target_dias = 0

        # --- 5. APLICAR LÓGICA DE FINES DE SEMANA ---
        vars_findes = []
        for lunes, dias in findes.items():
            # Un finde es trabajable si no tiene licencia ni FRANCO_FORZADO en todos sus días
            dias_habilitados = []
            for d in dias:
                if d in emp.dias_licencia:
                    continue
                fecha_d_str = (fecha_inicio_dt + timedelta(days=d)).isoformat()
                p_franco = _re.resolver_parametros_regla('FRANCO_FORZADO', emp.nombre, fecha_d_str, reglas_servicio, emp.reglas, ajustes_reglas)
                if _re.regla_existe(p_franco) and not _re.regla_suspendida(p_franco):
                    continue
                dias_habilitados.append(d)
            
            if not dias_habilitados:
                continue
            
            v_este_finde = modelo.NewBoolVar(f'traba_f_exacto_finde_dia_{emp.nombre}_{lunes}')
            pool_f = []
            for d in dias_habilitados:
                for td in ["Finde_Feriado"]:
                    for t in demanda_turnos.get(td, {}).keys():
                        if (emp.nombre, d, t) in turnos_vars:
                            pool_f.append(turnos_vars[(emp.nombre, d, t)])
            
            if pool_f:
                modelo.AddMaxEquality(v_este_finde, pool_f)
                vars_findes.append(v_este_finde)

        target_f_real = min(target_findes, len(vars_findes)) if vars_findes else 0

        if vars_findes:
            if modo == "HARD":
                modelo.Add(sum(vars_findes) == target_f_real)
            else: # SOFT
                if penalizaciones_ad_hoc is not None:
                    violation_under = modelo.NewIntVar(0, target_f_real, f'viol_under_findes_combo_{emp.nombre}')
                    violation_over = modelo.NewIntVar(0, len(vars_findes), f'viol_over_findes_combo_{emp.nombre}')
                    modelo.Add(sum(vars_findes) + violation_under - violation_over == target_f_real)
                    
                    violation = modelo.NewIntVar(0, len(vars_findes) + target_f_real, f'viol_findes_combo_{emp.nombre}')
                    modelo.Add(violation == violation_under + violation_over)
                    penalizaciones_ad_hoc.append(violation * peso_soft)

        # --- 6. APLICAR LÓGICA DE DÍA ESPECÍFICO ---
        # Si el empleado tiene ASIGNACION_FIJA en algún día de la semana objetivo,
        # esa asignación ya controla cuántas veces trabaja ese día — no aplicar la restricción
        # para evitar doble restricción conflictiva.
        tiene_asig_fija_en_dia = False
        for d_check in range(dias_del_bloque):
            fecha_d_check = fecha_inicio_dt + timedelta(days=d_check)
            if fecha_d_check.weekday() != dia_semana_target:
                continue
            if d_check in emp.dias_licencia:
                continue
            fecha_check_str = fecha_d_check.isoformat()
            p_asig = _re.resolver_parametros_regla('ASIGNACION_FIJA', emp.nombre, fecha_check_str, reglas_servicio, emp.reglas, ajustes_reglas)
            if _re.regla_existe(p_asig) and not _re.regla_suspendida(p_asig):
                tiene_asig_fija_en_dia = True
                break

        if not tiene_asig_fija_en_dia:
            vars_dia = []
            for d in range(dias_del_bloque):
                fecha_d = fecha_inicio_dt + timedelta(days=d)
                if fecha_d.weekday() != dia_semana_target:
                    continue
                if d in emp.dias_licencia:
                    continue
                fecha_d_str = fecha_d.isoformat()
                p_franco = _re.resolver_parametros_regla('FRANCO_FORZADO', emp.nombre, fecha_d_str, reglas_servicio, emp.reglas, ajustes_reglas)
                if _re.regla_existe(p_franco) and not _re.regla_suspendida(p_franco):
                    continue

                v_este_dia = modelo.NewBoolVar(f'traba_dia_exacto_finde_dia_{emp.nombre}_{dia_semana_target}_{d}')
                pool_d = []
                for t in turnos_dict.keys():
                    if (emp.nombre, d, t) in turnos_vars:
                        pool_d.append(turnos_vars[(emp.nombre, d, t)])

                if pool_d:
                    modelo.AddMaxEquality(v_este_dia, pool_d)
                    vars_dia.append(v_este_dia)

            target_d_real = min(target_dias, len(vars_dia)) if vars_dia else 0

            if vars_dia:
                if modo == "HARD":
                    modelo.Add(sum(vars_dia) == target_d_real)
                else: # SOFT
                    if penalizaciones_ad_hoc is not None:
                        violation_under = modelo.NewIntVar(0, target_d_real, f'viol_under_dia_combo_{emp.nombre}_{dia_semana_target}')
                        violation_over = modelo.NewIntVar(0, len(vars_dia), f'viol_over_dia_combo_{emp.nombre}_{dia_semana_target}')
                        modelo.Add(sum(vars_dia) + violation_under - violation_over == target_d_real)
                        
                        violation = modelo.NewIntVar(0, len(vars_dia) + target_d_real, f'viol_dia_combo_{emp.nombre}_{dia_semana_target}')
                        modelo.Add(violation == violation_under + violation_over)
                        penalizaciones_ad_hoc.append(violation * peso_soft)

