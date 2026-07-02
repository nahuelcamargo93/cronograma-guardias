"""
restricciones/double/manejo_findes.py — Regla Maestra de Fines de Semana.
Unifica Finde Largo Reglamentario, Findes Completos, Medios y Día Específico.
Regla: MANEJO_FINDES
"""
from datetime import date, timedelta
from restricciones.cargador import add_hard
from restricciones.hard._utils import is_finde
import rule_engine as _re
from database.connection import get_connection

_MAPA = {"lunes": 0, "martes": 1, "miercoles": 2, "jueves": 3,
         "viernes": 4, "sabado": 5, "domingo": 6}
_NORM = str.maketrans("éáíóúÉÁÍÓÚ", "eaiouEAIOU")


def apply(modelo, ctx) -> None:
    fecha_inicio_dt = date.fromisoformat(ctx.fecha_inicio)
    ref_fecha = ctx.fecha_inicio

    # --- Lógica de Nivelación Histórica (Pre-procesamiento) ---
    completos_historicos = {}
    medios_historicos = {}
    target_c_historicos = {}
    target_m_historicos = {}

    regla_serv = ctx.reglas_servicio.get('MANEJO_FINDES')
    nivelacion_config = regla_serv.get('nivelacion_historica') if isinstance(regla_serv, dict) else None

    if nivelacion_config and nivelacion_config.get('activo'):
        tipo_niv = nivelacion_config.get('tipo', 'ANUAL').upper()
        fecha_inicio_niv_str = nivelacion_config.get('fecha_inicio')
        
        if not fecha_inicio_niv_str:
            if tipo_niv == 'ANUAL':
                fecha_inicio_niv_str = f"{fecha_inicio_dt.year}-01-01"
            else:
                fecha_inicio_niv_str = None
        
        if fecha_inicio_niv_str:
            fecha_fin_hist_dt = fecha_inicio_dt - timedelta(days=1)
            fecha_fin_hist_str = fecha_fin_hist_dt.isoformat()
            
            if fecha_inicio_niv_str <= fecha_fin_hist_str:
                with get_connection() as conn:
                    cronos = conn.execute("""
                        SELECT DISTINCT c.id, c.fecha_inicio, c.fecha_fin
                        FROM cronogramas c
                        JOIN guardias g ON c.id = g.cronograma_id
                        JOIN personal p ON g.nombre = p.nombre
                        WHERE p.servicio_id = ?
                          AND c.estado = 'aprobado'
                          AND c.fecha_inicio >= ?
                          AND c.fecha_fin <= ?
                        ORDER BY c.fecha_inicio
                    """, (ctx.servicio_id, fecha_inicio_niv_str, fecha_fin_hist_str)).fetchall()
                
                if cronos:
                    crono_ids = [c[0] for c in cronos]
                    with get_connection() as conn:
                        placeholders = ",".join("?" for _ in crono_ids)
                        guardias_hist = conn.execute(f"""
                            SELECT g.nombre, g.fecha, g.cronograma_id
                            FROM guardias g
                            JOIN personal p ON g.nombre = p.nombre
                            WHERE g.cronograma_id IN ({placeholders})
                              AND g.es_finde = 1
                              AND p.servicio_id = ?
                        """, crono_ids + [ctx.servicio_id]).fetchall()
                        
                        licencias_raw = conn.execute("""
                            SELECT l.nombre, l.tipo, l.fecha_inicio, l.fecha_fin
                            FROM licencias l
                            JOIN personal p ON l.nombre = p.nombre
                            WHERE p.servicio_id = ?
                        """, (ctx.servicio_id,)).fetchall()
                    
                    licencias_by_emp = {}
                    for nom, tipo, fi, ff in licencias_raw:
                        licencias_by_emp.setdefault(nom, []).append((date.fromisoformat(fi), date.fromisoformat(ff)))

                    guardias_por_finde = {}
                    for nom, fecha_str, c_id in guardias_hist:
                        f_dt = date.fromisoformat(fecha_str)
                        wd = f_dt.weekday()
                        if wd in (5, 6):
                            lunes_dt = f_dt - timedelta(days=wd)
                            lunes_str = lunes_dt.isoformat()
                            guardias_por_finde.setdefault(nom, {}).setdefault((c_id, lunes_str), set()).add(wd)
                    
                    for nom, findes_dict in guardias_por_finde.items():
                        c_count = 0
                        m_count = 0
                        for (c_id, lunes_str), wds in findes_dict.items():
                            if len(wds) >= 2:
                                c_count += 1
                            elif len(wds) == 1:
                                m_count += 1
                        completos_historicos[nom] = c_count
                        medios_historicos[nom] = m_count
                    
                    with get_connection() as conn:
                        activos_crono = {}
                        placeholders = ",".join("?" for _ in crono_ids)
                        rows_activos = conn.execute(f"""
                            SELECT DISTINCT g.nombre, g.cronograma_id
                            FROM guardias g
                            JOIN personal p ON g.nombre = p.nombre
                            WHERE g.cronograma_id IN ({placeholders})
                              AND p.servicio_id = ?
                        """, crono_ids + [ctx.servicio_id]).fetchall()
                        for nom, c_id in rows_activos:
                            activos_crono.setdefault(c_id, set()).add(nom)

                    for c_id, c_ini_str, c_fin_str in cronos:
                        c_ini_dt = date.fromisoformat(c_ini_str)
                        c_fin_dt = date.fromisoformat(c_fin_str)
                        c_dias = (c_fin_dt - c_ini_dt).days + 1
                        
                        c_findes = {}
                        for d in range(c_dias):
                            fd = c_ini_dt + timedelta(days=d)
                            wd = fd.weekday()
                            if wd in (5, 6):
                                lunes_str = (fd - timedelta(days=wd)).isoformat()
                                c_findes.setdefault(lunes_str, []).append(fd)
                        
                        for emp in ctx.empleados:
                            if emp.nombre not in activos_crono.get(c_id, set()):
                                continue
                            
                            emp_lics = licencias_by_emp.get(emp.nombre, [])
                            
                            def _disponible_hist(dia_dt):
                                for l_ini, l_fin in emp_lics:
                                    if l_ini <= dia_dt <= l_fin:
                                        return False
                                return True
                            
                            k_disp_hist = sum(
                                1 for _, dias_f in c_findes.items()
                                if any(_disponible_hist(d) for d in dias_f)
                            )
                            
                            emp_params = _re.resolver_parametros_regla(
                                'MANEJO_FINDES', emp.nombre, c_ini_str,
                                ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
                            )
                            if _re.regla_existe(emp_params) and not _re.regla_suspendida(emp_params):
                                emp_conf_disp = emp_params.get('por_disponibilidad', {}).get(str(k_disp_hist), {})
                                target_c_hist = emp_conf_disp.get('completos', 0)
                                target_m_hist = emp_conf_disp.get('medios', 0)
                                
                                target_c_historicos[emp.nombre] = target_c_historicos.get(emp.nombre, 0) + target_c_hist
                                target_m_historicos[emp.nombre] = target_m_historicos.get(emp.nombre, 0) + target_m_hist

    def crear_var_flr(emp, lunes, d_inicio, prefijo):
        dias_flr = [d_inicio, d_inicio + 1, d_inicio + 2, d_inicio + 3]
        for d_e in dias_flr:
            if d_e >= ctx.dias:
                return None
            if d_e >= 0:
                if d_e in emp.dias_licencia:
                    return None
            else:
                # d_e < 0 (mes anterior): si trabajó ese día, no es un bloque libre válido
                fecha_d_str = (fecha_inicio_dt + timedelta(days=d_e)).isoformat()
                hist_emp = ctx.historial_semana_previa.get(emp.nombre, []) if ctx.historial_semana_previa else []
                trabajado_d = any(h['fecha'] == fecha_d_str and h.get('horas', 0) > 0 for h in hist_emp)
                if trabajado_d:
                    return None

        # Verificar si todos los días de este bloque libre de 4 días tienen franco forzado activo
        # (por ende, el bloque libre fue configurado explícitamente por el usuario)
        def _tiene_franco_forzado(d_idx):
            if d_idx < 0 or d_idx >= ctx.dias:
                return False
            fecha_d_str = (fecha_inicio_dt + timedelta(days=d_idx)).isoformat()
            p = _re.resolver_parametros_regla(
                'FRANCO_FORZADO', emp.nombre, fecha_d_str,
                ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
            )
            tiene_franco = _re.regla_existe(p) and not _re.regla_suspendida(p)

            tiene_fija_fecha = False
            params_fija = _re.resolver_parametros_regla(
                'ASIGNACION_FIJA', emp.nombre, fecha_d_str,
                ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
            )
            if _re.regla_existe(params_fija) and isinstance(params_fija, list):
                for asig in params_fija:
                    if asig.get('Fecha') == fecha_d_str:
                        tiene_fija_fecha = True
                        break

            return tiene_franco and not tiene_fija_fecha

        forzado_por_usuario = all(_tiene_franco_forzado(d_e) for d_e in dias_flr)
        
        var_bloque = modelo.NewBoolVar(f'flr_{prefijo}_{emp.nombre}_{lunes}')
        flr_conds = []
        
        vars_bloque_flr = []
        for d_e in dias_flr:
            if d_e < 0 or d_e >= ctx.dias:
                continue
            es_f = is_finde(d_e, ctx.offset_dia, ctx.feriados)
            for t in ctx.demanda_turnos.get("Finde_Feriado" if es_f else "Semana", {}).keys():
                if (emp.nombre, d_e, t) in ctx.turnos:
                    vars_bloque_flr.append(ctx.turnos[(emp.nombre, d_e, t)])
                    
        libre_flr = modelo.NewBoolVar(f'libre_{prefijo}_{emp.nombre}_{lunes}')
        if vars_bloque_flr:
            modelo.Add(sum(vars_bloque_flr) == 0).OnlyEnforceIf(libre_flr)
            modelo.Add(sum(vars_bloque_flr) > 0).OnlyEnforceIf(libre_flr.Not())
        else:
            modelo.Add(libre_flr == 1)
        flr_conds.append(libre_flr)
        
        d_prev = d_inicio - 1
        if d_prev >= 0:
            es_f_p = is_finde(d_prev, ctx.offset_dia, ctx.feriados)
            vars_prev = [
                ctx.turnos[(emp.nombre, d_prev, t)]
                for t in ctx.demanda_turnos.get("Finde_Feriado" if es_f_p else "Semana", {}).keys()
                if (emp.nombre, d_prev, t) in ctx.turnos
            ]
            if vars_prev:
                prev_ok = modelo.NewBoolVar(f'prev_{prefijo}_{emp.nombre}_{lunes}')
                modelo.AddBoolOr(vars_prev).OnlyEnforceIf(prev_ok)
                modelo.AddBoolAnd([v.Not() for v in vars_prev]).OnlyEnforceIf(prev_ok.Not())
                flr_conds.append(prev_ok)
            else:
                flr_conds.append(modelo.NewConstant(0))
        else:
            # d_prev < 0 (pertenece al mes anterior)
            fecha_prev_str = (fecha_inicio_dt + timedelta(days=d_prev)).isoformat()
            hist_emp = ctx.historial_semana_previa.get(emp.nombre, []) if ctx.historial_semana_previa else []
            trabajo_previo = any(h['fecha'] == fecha_prev_str and h.get('horas', 0) > 0 for h in hist_emp)
            if trabajo_previo:
                flr_conds.append(modelo.NewConstant(1))
            else:
                if ctx.historial_semana_previa:
                    flr_conds.append(modelo.NewConstant(0))
                else:
                    flr_conds.append(modelo.NewConstant(1))
            
        d_post = d_inicio + 4
        if d_post < ctx.dias:
            es_f_po = is_finde(d_post, ctx.offset_dia, ctx.feriados)
            vars_post = [
                ctx.turnos[(emp.nombre, d_post, t)]
                for t in ctx.demanda_turnos.get("Finde_Feriado" if es_f_po else "Semana", {}).keys()
                if (emp.nombre, d_post, t) in ctx.turnos
            ]
            if vars_post:
                post_ok = modelo.NewBoolVar(f'post_{prefijo}_{emp.nombre}_{lunes}')
                modelo.AddBoolOr(vars_post).OnlyEnforceIf(post_ok)
                modelo.AddBoolAnd([v.Not() for v in vars_post]).OnlyEnforceIf(post_ok.Not())
                flr_conds.append(post_ok)
            else:
                flr_conds.append(modelo.NewConstant(0))
        else:
            flr_conds.append(modelo.NewConstant(1))
            
        modelo.AddBoolAnd(flr_conds).OnlyEnforceIf(var_bloque)
        modelo.AddBoolOr([v.Not() if hasattr(v, 'Not') else v == 0 for v in flr_conds]).OnlyEnforceIf(var_bloque.Not())
        
        if forzado_por_usuario:
            modelo.Add(var_bloque == 1)
            
        return var_bloque

    for emp in ctx.empleados:
        params = _re.resolver_parametros_regla(
            'MANEJO_FINDES', emp.nombre, ref_fecha,
            ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
        )
        if not _re.regla_existe(params) or _re.regla_suspendida(params):
            continue

        modo = params.get('modo', 'HARD').upper()
        peso_soft = params.get('peso_soft', 100000)
        flr_permitidos = params.get('flr_permitidos', ["jd", "vl", "sm"])

        dia_conf = params.get('dia_semana', None)
        dia_target = None
        if dia_conf is not None:
            dia_str = str(dia_conf).lower().translate(_NORM)
            dia_target = _MAPA.get(dia_str, int(dia_conf) if str(dia_conf).isdigit() else 4)

        # 1. Agrupar findes por semana
        findes = {}
        for d in range(ctx.dias):
            wd = (fecha_inicio_dt + timedelta(days=d)).weekday()
            if wd in (5, 6):
                fd = fecha_inicio_dt + timedelta(days=d)
                lunes = (fd - timedelta(days=wd)).isoformat()
                findes.setdefault(lunes, []).append((d, wd))

        def _disponible(d_idx):
            if d_idx in emp.dias_licencia:
                return False
            fecha_d_str = (fecha_inicio_dt + timedelta(days=d_idx)).isoformat()
            p = _re.resolver_parametros_regla(
                'FRANCO_FORZADO', emp.nombre, fecha_d_str,
                ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
            )
            tiene_franco = _re.regla_existe(p) and not _re.regla_suspendida(p)

            tiene_fija_fecha = False
            params_fija = _re.resolver_parametros_regla(
                'ASIGNACION_FIJA', emp.nombre, fecha_d_str,
                ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
            )
            if _re.regla_existe(params_fija) and isinstance(params_fija, list):
                for asig in params_fija:
                    if asig.get('Fecha') == fecha_d_str:
                        tiene_fija_fecha = True
                        break

            return not (tiene_franco and not tiene_fija_fecha)

        def _tiene_flr_forzado(lunes, dias_f):
            d_sat = next((d for d, w in dias_f if w == 5), None)
            if d_sat is None:
                return False
            
            flr_offsets = {
                "jd": -2, # Jueves a Domingo
                "vl": -1, # Viernes a Lunes
                "sm": 0   # Sábado a Martes
            }
            
            for pref in flr_permitidos:
                offset = flr_offsets.get(pref)
                if offset is None:
                    continue
                d_inicio = d_sat + offset
                dias_flr = [d_inicio, d_inicio + 1, d_inicio + 2, d_inicio + 3]
                
                fuera_de_rango = False
                tiene_licencia = False
                for d_e in dias_flr:
                    if d_e < 0 or d_e >= ctx.dias:
                        fuera_de_rango = True
                        break
                    if d_e in emp.dias_licencia:
                        tiene_licencia = True
                        break
                if fuera_de_rango or tiene_licencia:
                    continue
                
                todos_con_franco = True
                for d_e in dias_flr:
                    fecha_d_str = (fecha_inicio_dt + timedelta(days=d_e)).isoformat()
                    p = _re.resolver_parametros_regla(
                        'FRANCO_FORZADO', emp.nombre, fecha_d_str,
                        ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
                    )
                    tiene_franco = _re.regla_existe(p) and not _re.regla_suspendida(p)

                    tiene_fija_fecha = False
                    params_fija = _re.resolver_parametros_regla(
                        'ASIGNACION_FIJA', emp.nombre, fecha_d_str,
                        ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
                    )
                    if _re.regla_existe(params_fija) and isinstance(params_fija, list):
                        for asig in params_fija:
                            if asig.get('Fecha') == fecha_d_str:
                                tiene_fija_fecha = True
                                break

                    if not (tiene_franco and not tiene_fija_fecha):
                        todos_con_franco = False
                        break

                if todos_con_franco:
                    return True
            return False

        # Calcular disponibilidad de fines de semana completos
        k_disp = sum(
            1 for lunes, dias_f in findes.items() 
            if any(_disponible(d) for d, _ in dias_f) or _tiene_flr_forzado(lunes, dias_f)
        )

        # Targets de configuración basados en disponibilidad
        conf_disp = params.get('por_disponibilidad', {}).get(str(k_disp), {})
        target_flr = conf_disp.get('flr', 0)
        target_c = conf_disp.get('completos', 0)
        target_m = conf_disp.get('medios', 0)

        vars_flr = []
        vars_completo = []
        vars_medio = []

        for lunes, dias_f in findes.items():
            d_sat = next((d for d, w in dias_f if w == 5), None)
            d_sun = next((d for d, w in dias_f if w == 6), None)
            if d_sat is None or d_sun is None:
                continue

            # Pool de turnos fin de semana
            pool_sat = [
                ctx.turnos[(emp.nombre, d_sat, t)]
                for t in ctx.demanda_turnos.get("Finde_Feriado", {}).keys()
                if (emp.nombre, d_sat, t) in ctx.turnos
            ]
            v_sat = modelo.NewBoolVar(f'sat_{emp.nombre}_{lunes}')
            if pool_sat:
                modelo.AddBoolOr(pool_sat).OnlyEnforceIf(v_sat)
                modelo.AddBoolAnd([v.Not() for v in pool_sat]).OnlyEnforceIf(v_sat.Not())
            else:
                modelo.Add(v_sat == 0)

            pool_sun = [
                ctx.turnos[(emp.nombre, d_sun, t)]
                for t in ctx.demanda_turnos.get("Finde_Feriado", {}).keys()
                if (emp.nombre, d_sun, t) in ctx.turnos
            ]
            v_sun = modelo.NewBoolVar(f'sun_{emp.nombre}_{lunes}')
            if pool_sun:
                modelo.AddBoolOr(pool_sun).OnlyEnforceIf(v_sun)
                modelo.AddBoolAnd([v.Not() for v in pool_sun]).OnlyEnforceIf(v_sun.Not())
            else:
                modelo.Add(v_sun == 0)

            # --- Lógica de FLR (Finde Largo Reglamentario) ---
            tiene_flr = modelo.NewBoolVar(f'flr_{emp.nombre}_{lunes}')
            
            v_flr_j_d = crear_var_flr(emp, lunes, d_sat - 2, "jd") if "jd" in flr_permitidos else None # Jueves a Domingo
            v_flr_v_l = crear_var_flr(emp, lunes, d_sat - 1, "vl") if "vl" in flr_permitidos else None # Viernes a Lunes
            v_flr_s_m = crear_var_flr(emp, lunes, d_sat, "sm")     if "sm" in flr_permitidos else None # Sábado a Martes
            
            opciones_activas = []
            if v_flr_j_d is not None:
                opciones_activas.append(v_flr_j_d)
                if ctx.flr_tracker is not None:
                    ctx.flr_tracker[(emp.nombre, d_sat - 2)] = v_flr_j_d
                ctx.penalizaciones_soft.append(v_flr_j_d * 3000)
                
            if v_flr_v_l is not None:
                opciones_activas.append(v_flr_v_l)
                if ctx.flr_tracker is not None:
                    ctx.flr_tracker[(emp.nombre, d_sat - 1)] = v_flr_v_l
                ctx.penalizaciones_soft.append(v_flr_v_l * 1000)
                
            if v_flr_s_m is not None:
                opciones_activas.append(v_flr_s_m)
                if ctx.flr_tracker is not None:
                    ctx.flr_tracker[(emp.nombre, d_sat)] = v_flr_s_m
                
            if opciones_activas:
                modelo.Add(sum(opciones_activas) <= 1)
                modelo.Add(tiene_flr == sum(opciones_activas))
            else:
                modelo.Add(tiene_flr == 0)
                
            vars_flr.append(tiene_flr)

            # --- Lógica de Completos y Medios ---
            v_comp = modelo.NewBoolVar(f'f_comp_{emp.nombre}_{lunes}')
            modelo.AddBoolAnd([v_sat, v_sun]).OnlyEnforceIf(v_comp)
            modelo.AddBoolOr([v_sat.Not(), v_sun.Not()]).OnlyEnforceIf(v_comp.Not())
            
            # Si tiene FLR, no puede contar como completo ni medio (ya que no trabaja), 
            # pero matemáticamente v_comp ya será 0 porque v_sat y v_sun serán 0.
            vars_completo.append(v_comp)

            v_med = modelo.NewBoolVar(f'f_med_{emp.nombre}_{lunes}')
            modelo.Add(v_sat + v_sun - 2 * v_comp == v_med)
            vars_medio.append(v_med)

        # Aplicar restricciones conjuntas
        def _aplicar_restriccion(target_val, variables, nombre_logico, valor_historico=0):
            if not variables: return
            if modo == "HARD":
                add_hard(modelo, ctx,
                         modelo.Add(sum(variables) + valor_historico == target_val),
                         f"{emp.nombre}_{nombre_logico}")
            else:
                if nombre_logico == "flr":
                    violation_under = modelo.NewIntVar(0, target_val, f'viol_under_{nombre_logico}_{emp.nombre}')
                    modelo.Add(sum(variables) + violation_under >= target_val)
                    ctx.penalizaciones_soft.append(violation_under * peso_soft)
                else:
                    max_over = len(variables) + max(0, valor_historico - target_val) + 10
                    violation_over = modelo.NewIntVar(0, max_over, f'viol_over_{nombre_logico}_{emp.nombre}')
                    modelo.Add(sum(variables) + valor_historico - violation_over <= target_val)
                    ctx.penalizaciones_soft.append(violation_over * peso_soft)
                    
                    if target_val > 0:
                        max_under = target_val + 10
                        violation_under = modelo.NewIntVar(0, max_under, f'viol_under_{nombre_logico}_{emp.nombre}')
                        modelo.Add(sum(variables) + valor_historico + violation_under >= target_val)
                        ctx.penalizaciones_soft.append(violation_under * peso_soft)


        # Cargar históricos y targets acumulados
        c_hist = completos_historicos.get(emp.nombre, 0)
        m_hist = medios_historicos.get(emp.nombre, 0)
        tc_hist = target_c_historicos.get(emp.nombre, 0)
        tm_hist = target_m_historicos.get(emp.nombre, 0)

        target_c_acum = target_c + tc_hist
        target_m_acum = target_m + tm_hist

        _aplicar_restriccion(target_flr, vars_flr, "flr")
        _aplicar_restriccion(target_c_acum, vars_completo, "finde_comp", valor_historico=c_hist)
        _aplicar_restriccion(target_m_acum, vars_medio, "finde_med", valor_historico=m_hist)

        # --- Lógica de Día Específico Opcional ---
        if dia_target is None:
            continue

        k_dia = 0
        for d in range(ctx.dias):
            if (fecha_inicio_dt + timedelta(days=d)).weekday() != dia_target: continue
            if d in emp.dias_licencia: continue
            k_dia += 1

        target_d = conf_disp.get('dias_especificos', 0)
        
        vars_dia = []
        for d in range(ctx.dias):
            if (fecha_inicio_dt + timedelta(days=d)).weekday() != dia_target: continue
            if d in emp.dias_licencia: continue
            v = modelo.NewBoolVar(f'traba_dia_{emp.nombre}_{dia_target}_{d}')
            pool = [ctx.turnos[(emp.nombre, d, t)]
                    for t in ctx.turnos_dict.keys()
                    if (emp.nombre, d, t) in ctx.turnos]
            if pool:
                modelo.AddBoolOr(pool).OnlyEnforceIf(v)
                modelo.AddBoolAnd([p.Not() for p in pool]).OnlyEnforceIf(v.Not())
                vars_dia.append(v)
                
        _aplicar_restriccion(target_d, vars_dia, f"dia_{dia_target}")
