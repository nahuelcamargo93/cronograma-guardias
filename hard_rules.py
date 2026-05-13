from datetime import date, timedelta
from data import FECHA_INICIO, FECHA_FIN, DEBUG_LOGS, DEBUG_DISABLE_SEGUIMIENTO, DEBUG_DISABLE_DESCANSO_NOCHE, DEBUG_DISABLE_MAX_HORAS, DIA_DEL_PADRE, DIA_DE_LA_MADRE
import db as _db
import rule_engine as _re


def _get_licencias(): return _db.LAR, _db.LPP

def aplicar_reglas_duras(modelo, turnos, df_personal, demanda_turnos, metadata_turnos, demanda_req, ajustes_demanda, dias_del_bloque, feriados, offset_dia, num_semanas, historial_semana_previa=None, flr_tracker=None, servicio_id=1):
    # Cargar el motor de reglas desde la BD
    reglas_servicio = _db.cargar_reglas_servicio(servicio_id)
    reglas_personal = _db.cargar_reglas_personal(servicio_id)
    ajustes_reglas_personal = _db.cargar_ajustes_reglas_personal(FECHA_INICIO, FECHA_FIN)
    
    # Validar regla obligatoria MAX_HORAS_SEMANA
    if 'MAX_HORAS_SEMANA' not in reglas_servicio:
        raise ValueError("❌ ERROR CRÍTICO: La regla 'MAX_HORAS_SEMANA' no está configurada en la base de datos para este servicio.")
    
    limite_horas_global = reglas_servicio['MAX_HORAS_SEMANA'].get('limite')
    if limite_horas_global is None:
        raise ValueError("❌ ERROR CRÍTICO: El parámetro 'limite' de la regla 'MAX_HORAS_SEMANA' no está definido en el JSON de la base de datos.")

    if 'DESC_POST_NOCHE' not in reglas_servicio:
        raise ValueError("❌ ERROR CRÍTICO: La regla 'DESC_POST_NOCHE' no está configurada en la base de datos para este servicio.")
    

    # Semanas de referencia base (originalmente el sistema fue calibrado para 4 semanas)
    SEMANAS_BASE = 4
    # 0. LAR / LPP: bloquear todos los turnos en días de licencia
    fecha_inicio_dt = date.fromisoformat(FECHA_INICIO)

    def get_dias_bloqueados(nombre):
        """Set de índices de día (0-based) en que la persona está de LAR, LPP o día libre obligatorio."""
        bloqueados = set()
        for licencias in _get_licencias():
            for (ini_str, fin_str) in licencias.get(nombre, []):
                ini = date.fromisoformat(ini_str)
                fin = date.fromisoformat(fin_str)
                for d in range(dias_del_bloque):
                    if ini <= fecha_inicio_dt + timedelta(days=d) <= fin:
                        bloqueados.add(d)
                        
        # Regla CUMPLEANOS_LIBRE
        params_cumple = _re.resolver_parametros_regla(
            'CUMPLEANOS_LIBRE', nombre, FECHA_INICIO,
            reglas_servicio, reglas_personal, ajustes_reglas_personal
        )
        if _re.regla_existe(params_cumple):
            persona_row = df_personal[df_personal['Nombre'] == nombre].iloc[0]
            cumple = persona_row.get('fecha_cumpleanos')
            if cumple and isinstance(cumple, str) and len(cumple) >= 5:
                try:
                    parts = cumple.split('-')
                    if len(parts) >= 3:
                        m, d_c = int(parts[1]), int(parts[2])
                        for d in range(dias_del_bloque):
                            dia_actual = fecha_inicio_dt + timedelta(days=d)
                            if dia_actual.month == m and dia_actual.day == d_c:
                                bloqueados.add(d)
                except ValueError:
                    pass

        # Regla DIA_MADRE_PADRE_LIBRE
        params_especial = _re.resolver_parametros_regla(
            'DIA_MADRE_PADRE_LIBRE', nombre, FECHA_INICIO,
            reglas_servicio, reglas_personal, ajustes_reglas_personal
        )
        if _re.regla_existe(params_especial):
            persona_row = df_personal[df_personal['Nombre'] == nombre].iloc[0]
            es_madre = persona_row.get('es_madre', 0) == 1
            es_padre = persona_row.get('es_padre', 0) == 1
            
            fechas_especiales = []
            if es_madre and DIA_DE_LA_MADRE:
                fechas_especiales.append(date.fromisoformat(DIA_DE_LA_MADRE))
            if es_padre and DIA_DEL_PADRE:
                fechas_especiales.append(date.fromisoformat(DIA_DEL_PADRE))
                
            for fe in fechas_especiales:
                for d in range(dias_del_bloque):
                    if fecha_inicio_dt + timedelta(days=d) == fe:
                        bloqueados.add(d)

        return bloqueados

    licencias_semanales = {}
    for index, persona in df_personal.iterrows():
        nombre = persona['Nombre']
        bloqueados = get_dias_bloqueados(nombre)
        for d in bloqueados:
            tipos_dia = ["Semana", "Finde_Feriado"]
            for td in tipos_dia:
                for t in demanda_turnos.get(td, {}).keys():
                    if (nombre, d, t) in turnos:
                        modelo.Add(turnos[(nombre, d, t)] == 0)
        
        if DEBUG_LOGS and bloqueados:
            for d in bloqueados:
                sem = d // 7
                licencias_semanales.setdefault(sem, set()).add(nombre)

    if DEBUG_LOGS:
        print("\n--- DIAGNÓSTICO DE LICENCIAS ---")
        for sem, nombres in sorted(licencias_semanales.items()):
            print(f"Semana {sem}: {len(nombres)} personas de licencia ({', '.join(nombres)})")

    # Agrupar días del bloque por semana calendario ISO
    semanas_calendario = {}
    for d in range(dias_del_bloque):
        fecha_d = fecha_inicio_dt + timedelta(days=d)
        iso_year, iso_week, iso_weekday = fecha_d.isocalendar()
        semanas_calendario.setdefault((iso_year, iso_week), []).append((d, fecha_d))

    # 1. MAX_TURNOS: límite de un tipo de turno específico por bloque semanal
    # NO_NOCHES queda cubierto por EXCLUIR_TURNOS en personal_reglas.
    # Formato en DB: [{"turno": "Noche", "max_por_semana": 2}]
    for index, persona in df_personal.iterrows():
        nombre = persona['Nombre']
        historial_persona = historial_semana_previa.get(nombre, []) if historial_semana_previa else []
        
        for (iso_year, iso_week), days in semanas_calendario.items():
            first_day_of_week = days[0][1]
            fecha_lunes = (first_day_of_week - timedelta(days=first_day_of_week.isocalendar()[2] - 1)).isoformat()
            
            params = _re.resolver_parametros_regla(
                'MAX_TURNOS', nombre, fecha_lunes,
                reglas_servicio, reglas_personal, ajustes_reglas_personal
            )
            if not _re.regla_existe(params) or not isinstance(params, list):
                continue

            turnos_previos_en_semana = [h for h in historial_persona if date.fromisoformat(h['fecha']).isocalendar()[:2] == (iso_year, iso_week)]

            for restriccion in params:
                turno_tipo = restriccion.get('turno')
                max_sem    = restriccion.get('max_por_semana', 99)
                if not turno_tipo:
                    continue
                    
                previos_tipo = sum(1 for h in turnos_previos_en_semana if h['turno'] == turno_tipo)

                vars_tipo = [
                    turnos[(nombre, d, turno_tipo)]
                    for d, fd in days
                    if (nombre, d, turno_tipo) in turnos
                ]
                if vars_tipo or previos_tipo > 0:
                    modelo.Add(sum(vars_tipo) + previos_tipo <= max_sem)

    # 1b. EXCLUIR_TURNOS: prohibiciones individuales de turnos
    # Formato en DB: [{"turnos": ["Noche"], "dias": [0,1,2,3,4,5,6]}]
    for index, persona in df_personal.iterrows():
        nombre = persona['Nombre']
        for d in range(dias_del_bloque):
            fecha_d = (fecha_inicio_dt + timedelta(days=d)).isoformat()
            params_d = _re.resolver_parametros_regla(
                'EXCLUIR_TURNOS', nombre, fecha_d,
                reglas_servicio, reglas_personal, ajustes_reglas_personal
            )
            if not _re.regla_existe(params_d) or not isinstance(params_d, list):
                continue
            
            dia_semana = (d + offset_dia) % 7
            for excl in params_d:
                turnos_prohibidos = excl.get('turnos', [])
                dias_prohibidos = excl.get('dias', [0,1,2,3,4,5,6])
                if dia_semana in dias_prohibidos:
                    for t_prohibido in turnos_prohibidos:
                        if (nombre, d, t_prohibido) in turnos:
                            modelo.Add(turnos[(nombre, d, t_prohibido)] == 0)

    # 2. MIN_TURNOS: límite mínimo de un tipo de turno específico por bloque semanal
    # Formato en DB: [{"turno": "Mañana_UTI", "min_por_semana": 4}]
    for index, persona in df_personal.iterrows():
        nombre = persona['Nombre']
        historial_persona = historial_semana_previa.get(nombre, []) if historial_semana_previa else []

        for (iso_year, iso_week), days in semanas_calendario.items():
            first_day_of_week = days[0][1]
            fecha_lunes = (first_day_of_week - timedelta(days=first_day_of_week.isocalendar()[2] - 1)).isoformat()

            params = _re.resolver_parametros_regla(
                'MIN_TURNOS', nombre, fecha_lunes,
                reglas_servicio, reglas_personal, ajustes_reglas_personal
            )
            if not _re.regla_existe(params) or not isinstance(params, list):
                continue  # suspendida para esta persona/semana o no configurada

            turnos_previos_en_semana = [h for h in historial_persona if date.fromisoformat(h['fecha']).isocalendar()[:2] == (iso_year, iso_week)]
            bloqueados_persona = get_dias_bloqueados(nombre)

            for restriccion in params:
                turno_tipo = restriccion.get('turno')
                min_sem    = restriccion.get('min_por_semana', 0)
                if not turno_tipo or min_sem <= 0:
                    continue

                previos_tipo = sum(1 for h in turnos_previos_en_semana if h['turno'] == turno_tipo)

                vars_tipo = [
                    turnos[(nombre, d, turno_tipo)]
                    for d, fd in days
                    if (nombre, d, turno_tipo) in turnos and d not in bloqueados_persona
                ]
                
                if vars_tipo:
                    # Relajamos el mínimo si la persona está de licencia y no tiene suficientes días
                    min_efectivo = min(min_sem, len(vars_tipo) + previos_tipo)
                    modelo.Add(sum(vars_tipo) + previos_tipo >= min_efectivo)

    def time_to_float(t_str):
        h, m = map(int, t_str.split(':'))
        return h + m/60.0



    # 3. BALANCE DE CARGA HORARIA (DIAGNÓSTICO WFM)
    if DEBUG_LOGS:
        print("\n--- BALANCE DE CARGA HORARIA POR SEMANA (WFM) ---")
        for sem in range(num_semanas):
            horas_necesarias = 0
            for d in range(sem * 7, (sem + 1) * 7):
                es_f = ((d + offset_dia) % 7) >= 5 or d in feriados
                tipo_dia = "Finde_Feriado" if es_f else "Semana"
                fecha_actual_iso = (fecha_inicio_dt + timedelta(days=d)).isoformat()
                dia_semana_actual = (d + offset_dia) % 7
                
                for demanda in demanda_req.get(tipo_dia, []):
                    cantidad = demanda.get("cantidad_min") or 0
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
                            if dia_semana_actual not in dias_validos and d not in feriados:
                                cantidad = 0
                            else:
                                cantidad = ajuste_encontrado.get("cantidad_min") or 0
                        else:
                            cantidad = ajuste_encontrado.get("cantidad_min") or 0
                            
                    if cantidad > 0:
                        ds = time_to_float(demanda["hora_inicio"])
                        de = time_to_float(demanda["hora_fin"])
                        dur = de - ds if de > ds else (de + 24) - ds
                        horas_necesarias += cantidad * dur
            
            capacidad_max = 0
            ausentes_total = []
            ausentes_parcial = []
            for _, p in df_personal.iterrows():
                nombre = p['Nombre']
                bloqueados_sem = {d for d in get_dias_bloqueados(nombre) if d // 7 == sem}
                dias_libres = 7 - len(bloqueados_sem)
                if dias_libres == 0:
                    ausentes_total.append(nombre)
                else:
                    capacidad_max += limite_horas_global
                    if dias_libres < 7:
                        ausentes_parcial.append(f"{nombre}({dias_libres}d)")

            print(f"Semana {sem}: Necesarias {horas_necesarias} hs | Capacidad Max ({limite_horas_global}h) {capacidad_max} hs | Margen: {capacidad_max - horas_necesarias} hs")
            if ausentes_total:
                print(f"  [AUSENTES COMPLETOS] {', '.join(ausentes_total)}")
            if ausentes_parcial:
                print(f"  [AUSENTES PARCIALES] {', '.join(ausentes_parcial)}")
            if capacidad_max - horas_necesarias < 50:
                print(f"  [ALERTA] Margen muy bajo en Semana {sem}. Las restricciones de descanso podrian hacerla inviable.")


    # 4. COBERTURA DINÁMICA CON VALIDACIÓN WFM
    if DEBUG_LOGS: print("\n--- VALIDACIÓN DE COBERTURA WFM ---")
    for dia in range(dias_del_bloque):
        es_f = ((dia + offset_dia) % 7) >= 5 or dia in feriados
        tipo_dia = "Finde_Feriado" if es_f else "Semana"
        fecha_str = (fecha_inicio_dt + timedelta(days=dia)).strftime("%d/%m")
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
                    # Si es feriado, en la nueva arquitectura siempre aplica para Finde_Feriado
                    if dia_semana_actual not in dias_validos and dia not in feriados:
                        cantidad_min = 0
                        cantidad_max = 0
                    else:
                        cantidad_min = ajuste_encontrado.get("cantidad_min")
                        cantidad_max = ajuste_encontrado.get("cantidad_max")
                else:
                    cantidad_min = ajuste_encontrado.get("cantidad_min")
                    cantidad_max = ajuste_encontrado.get("cantidad_max")
            
            if (cantidad_min is None or cantidad_min == 0) and (cantidad_max is None or cantidad_max == 0):
                continue
                
            # El pool de variables se calcula ahora dinámicamente considerando cruces de medianoche

            pool_vars = []
            pool_posible = []
            
            d_abs_start = dia * 24 + time_to_float(demanda["hora_inicio"])
            d_h_end = time_to_float(demanda["hora_fin"])
            d_abs_end = dia * 24 + (d_h_end if (d_h_end > 0 or time_to_float(demanda["hora_inicio"]) == 0) else 24)

            for _, p in df_personal.iterrows():
                nombre = p['Nombre']
                
                # Turnos que podrían cubrir este bloque (Hoy o Ayer)
                for d_off in [0, -1]:
                    dia_t = dia + d_off
                    
                    if dia_t < 0:
                        # Revisar historial de la semana previa (Dia -1)
                        if historial_semana_previa:
                            # Buscar si trabajó un turno que cruza a hoy
                            prev_guards = historial_semana_previa.get(nombre, [])
                            fecha_ayer = (fecha_inicio_dt + timedelta(days=-1)).strftime("%Y-%m-%d")
                            for g in prev_guards:
                                if g['fecha'] == fecha_ayer:
                                    t_prev_nombre = g['turno']
                                    if t_prev_nombre in metadata_turnos:
                                        t_info = metadata_turnos[t_prev_nombre]
                                        ts_abs = -1 * 24 + time_to_float(t_info["hora_inicio"])
                                        te_abs = ts_abs + t_info["horas"]
                                        if ts_abs <= d_abs_start + 0.01 and te_abs >= d_abs_end - 0.01:
                                            # Es una constante, no una variable del modelo
                                            # Pero como estamos en el bloque de 'pool_vars' del modelo, 
                                            # si el historial ya cubre 1 cupo, deberíamos restar 1 a la demanda?
                                            # O simplemente añadir una constante 1 al sum(pool_vars)?
                                            pool_vars.append(1) 
                                            pool_posible.append(f"{nombre}(H:{t_prev_nombre})")
                        continue

                    if dia_t in get_dias_bloqueados(nombre):
                        continue

                    for t_nombre, t_info in metadata_turnos.items():
                        if t_info["puesto_id"] == demanda["puesto_id"]:
                            # Validar si el turno existe en el modelo para ese dia
                            if (nombre, dia_t, t_nombre) in turnos:
                                ts_abs = dia_t * 24 + time_to_float(t_info["hora_inicio"])
                                te_abs = ts_abs + t_info["horas"]
                                
                                if ts_abs <= d_abs_start + 0.01 and te_abs >= d_abs_end - 0.01:
                                    pool_vars.append(turnos[(nombre, dia_t, t_nombre)])
                                    pool_posible.append(f"{nombre}(d{dia_t}:{t_nombre})")

            if cantidad_min is not None and cantidad_min > 0:
                if len(pool_posible) < cantidad_min:
                    print(f"[ERROR CRITICO] Dia {fecha_str} ({tipo_dia}) Puesto {demanda['puesto']} {demanda['hora_inicio']}-{demanda['hora_fin']}: Se necesitan {cantidad_min} pero solo hay {len(pool_posible)} disponibles: {pool_posible}")
                
            if cantidad_min is not None:
                modelo.Add(sum(pool_vars) >= cantidad_min)
            
            if cantidad_max is not None:
                modelo.Add(sum(pool_vars) <= cantidad_max)

    # 5. LIMITE DE HORAS SEMANALES
    if DEBUG_DISABLE_MAX_HORAS:
        if DEBUG_LOGS: print("[MAX HORAS] Limite de horas semanales DESACTIVADO (DEBUG_DISABLE_MAX_HORAS=True)")
    else:
        for index, persona in df_personal.iterrows():
            nombre = persona['Nombre']
            historial_persona = historial_semana_previa.get(nombre, []) if historial_semana_previa else []

            for (iso_year, iso_week), days in semanas_calendario.items():
                first_day_of_week = days[0][1]
                fecha_lunes = (first_day_of_week - timedelta(days=first_day_of_week.isocalendar()[2] - 1)).isoformat()

                turnos_previos_en_semana = [h for h in historial_persona if date.fromisoformat(h['fecha']).isocalendar()[:2] == (iso_year, iso_week)]
                horas_previas = sum(h['horas'] for h in turnos_previos_en_semana)

                horas_semanales = []
                for d, fd in days:
                    es_finde = ((d + offset_dia) % 7) >= 5 or d in feriados
                    tipo_dia_h = "Finde_Feriado" if es_finde else "Semana"
                    for t in demanda_turnos.get(tipo_dia_h, {}).keys():
                        if (nombre, d, t) in turnos:
                            h_turno = 12 if (es_finde or t.startswith("Noche") or t.startswith("Dia")) else 6
                            horas_semanales.append(turnos[(nombre, d, t)] * h_turno)
                
                if horas_semanales or horas_previas > 0:
                    params = _re.resolver_parametros_regla(
                        'MAX_HORAS_SEMANA', nombre, fecha_lunes,
                        reglas_servicio, reglas_personal, ajustes_reglas_personal
                    )
                    if _re.regla_existe(params):
                        limite_semanal = params.get('limite', limite_horas_global) if isinstance(params, dict) else limite_horas_global
                        modelo.Add(sum(horas_semanales) + horas_previas <= limite_semanal)

    # 6. DESCANSO POST-NOCHE (Legacy)
    if DEBUG_DISABLE_DESCANSO_NOCHE:
        if DEBUG_LOGS: print("[DESCANSO NOCHE] Restriccion descanso post-noche DESACTIVADA (DEBUG_DISABLE_DESCANSO_NOCHE=True)")
    else:
        for index, persona in df_personal.iterrows():
            nombre = persona['Nombre']
            for d in range(dias_del_bloque - 1):
                if (nombre, d, "Noche") in turnos:
                    fecha_d = (fecha_inicio_dt + timedelta(days=d)).isoformat()
                    params = _re.resolver_parametros_regla(
                        'DESC_POST_NOCHE', nombre, fecha_d,
                        reglas_servicio, reglas_personal, ajustes_reglas_personal
                    )
                    if not _re.regla_existe(params):
                        continue  # suspendida para esta persona/fecha
                    horas_descanso = params.get('horas', 24) if isinstance(params, dict) else 24
                    if horas_descanso >= 24:
                        siguiente_dia_es_f = ((d+1 + offset_dia) % 7) >= 5 or (d+1 in feriados)
                        td_sig = "Finde_Feriado" if siguiente_dia_es_f else "Semana"
                        siguiente_dia = [turnos[(nombre, d+1, t)] for t in demanda_turnos.get(td_sig, {}).keys() if (nombre, d+1, t) in turnos]
                        for t_sig in siguiente_dia:
                            modelo.AddImplication(turnos[(nombre, d, "Noche")], t_sig.Not())

    # 6b. DESCANSO ENTRE TURNOS (General)
    for index, persona in df_personal.iterrows():
        nombre = persona['Nombre']
        for d in range(dias_del_bloque - 1):
            fecha_d = (fecha_inicio_dt + timedelta(days=d)).isoformat()
            params_rest = _re.resolver_parametros_regla(
                'DESCANSO_ENTRE_TURNOS', nombre, fecha_d,
                reglas_servicio, reglas_personal, ajustes_reglas_personal
            )
            if not _re.regla_existe(params_rest):
                continue
            
            min_descanso = params_rest.get('horas', 12) if isinstance(params_rest, dict) else 12
            
            # Turnos hoy
            es_f_hoy = ((d + offset_dia) % 7) >= 5 or d in feriados
            tipo_dia_hoy = "Finde_Feriado" if es_f_hoy else "Semana"
            turnos_hoy_nombres = [t for t in demanda_turnos.get(tipo_dia_hoy, {}).keys() if (nombre, d, t) in turnos]
            
            # Turnos mañana
            es_f_man = ((d+1 + offset_dia) % 7) >= 5 or (d+1 in feriados)
            tipo_dia_man = "Finde_Feriado" if es_f_man else "Semana"
            turnos_man_nombres = [t for t in demanda_turnos.get(tipo_dia_man, {}).keys() if (nombre, d+1, t) in turnos]
            
            for t1 in turnos_hoy_nombres:
                t1_info = metadata_turnos.get(t1)
                if not t1_info: continue
                t1_start = time_to_float(t1_info["hora_inicio"])
                t1_end = t1_start + t1_info["horas"]
                
                for t2 in turnos_man_nombres:
                    t2_info = metadata_turnos.get(t2)
                    if not t2_info: continue
                    t2_start = 24 + time_to_float(t2_info["hora_inicio"])
                    
                    if t2_start - t1_end < min_descanso - 0.01:
                        modelo.Add(turnos[(nombre, d, t1)] + turnos[(nombre, d+1, t2)] <= 1)
                        

    # 7. UN SOLO TURNO POR DÍA
    # Cubre todas las incompatibilidades: no se puede hacer mañana+noche,
    # tarde+noche, mañana_UTI+mañana_UCO, ni ninguna otra combinación el mismo día.
    # Excepción: si la persona tiene múltiples ASIGNACION_FIJA en el mismo día.
    mapa_dias = {"Lunes": 0, "Martes": 1, "Miercoles": 2, "Jueves": 3, "Viernes": 4, "Sabado": 5, "Domingo": 6}
    for index, persona in df_personal.iterrows():
        nombre = persona['Nombre']
        for d in range(dias_del_bloque):
            es_f = ((d + offset_dia) % 7) >= 5 or d in feriados
            tipo_dia = "Finde_Feriado" if es_f else "Semana"
            dia_semana = (d + offset_dia) % 7
            fecha_d_str = (fecha_inicio_dt + timedelta(days=d)).isoformat()
            
            fijos_hoy = 0
            params_asig = _re.resolver_parametros_regla(
                'ASIGNACION_FIJA', nombre, fecha_d_str,
                reglas_servicio, reglas_personal, ajustes_reglas_personal
            )
            if _re.regla_existe(params_asig) and isinstance(params_asig, list):
                for asig in params_asig:
                    if mapa_dias.get(asig.get('Dia')) == dia_semana:
                        fijos_hoy += 1
                        
            max_turnos_dia = max(1, fijos_hoy)

            todos_turnos_dia = [
                turnos[(nombre, d, t)]
                for t in demanda_turnos.get(tipo_dia, {}).keys()
                if (nombre, d, t) in turnos
            ]
            if todos_turnos_dia:
                modelo.Add(sum(todos_turnos_dia) <= max_turnos_dia)

    # 8. FINDE LARGO REGLAMENTARIO (FLR) - Movido a soft_rules.py como regla blanda de alta prioridad
    pass


    # 9. MÁXIMO DE HORAS POR MES CALENDARIO (Hard Limit)
    for index, persona in df_personal.iterrows():
        nombre = persona['Nombre']
        params_max_horas_cal = _re.resolver_parametros_regla(
            'MAX_HORAS_MES_CALENDARIO', nombre, FECHA_INICIO, 
            reglas_servicio, reglas_personal, ajustes_reglas_personal
        )
        if not _re.regla_suspendida(params_max_horas_cal):
            max_h_total_permitido = params_max_horas_cal.get('max_horas', 144) if isinstance(params_max_horas_cal, dict) else 144
            
            # Agrupar por mes calendario y aplicar tope pro-rata
            meses_en_bloque = {}
            for d in range(dias_del_bloque):
                m_key = (fecha_inicio_dt + timedelta(days=d)).strftime("%Y-%m")
                meses_en_bloque.setdefault(m_key, []).append(d)
                
            dias_bloqueados_p = get_dias_bloqueados(nombre)
            
            for m_key, dias_m in meses_en_bloque.items():
                # Horas efectivas en este mes
                vars_horas_m = []
                for d in dias_m:
                    es_f = ((d + offset_dia) % 7) >= 5 or d in feriados
                    tipo_dia_h = "Finde_Feriado" if es_f else "Semana"
                    for t in demanda_turnos.get(tipo_dia_h, {}).keys():
                        if (nombre, d, t) in turnos:
                            t_info = metadata_turnos.get(t)
                            h_turno = t_info["horas"] if t_info else 6
                            vars_horas_m.append(turnos[(nombre, d, t)] * h_turno)
                
                # Horas de licencia pro-rata (igual que en el reporte y soft_rules)
                dias_lic_m = [d for d in dias_m if d in dias_bloqueados_p]
                val_dia = 144.0 / dias_del_bloque
                horas_licencia_m = int(val_dia * len(dias_lic_m) + 0.5)
                
                # Tope pro-rata para este tramo del mes
                tope_pro_rata = int((max_h_total_permitido / dias_del_bloque) * len(dias_m) + 0.5)
                
                # Restricción: Efectivas + Licencia <= Tope
                if vars_horas_m:
                    modelo.Add(sum(vars_horas_m) + horas_licencia_m <= tope_pro_rata)
                    
    # 10. FIN_LICENCIA (Hard Limit)
    def get_dias_licencia_pura(nombre):
        dias = set()
        for licencias in _get_licencias():
            for (ini_str, fin_str) in licencias.get(nombre, []):
                ini = date.fromisoformat(ini_str)
                fin = date.fromisoformat(fin_str)
                for d in range(dias_del_bloque):
                    if ini <= fecha_inicio_dt + timedelta(days=d) <= fin:
                        dias.add(d)
        return dias

    for index, persona in df_personal.iterrows():
        nombre = persona['Nombre']
        params_fin_lic = _re.resolver_parametros_regla(
            'FIN_LICENCIA', nombre, FECHA_INICIO,
            reglas_servicio, reglas_personal, ajustes_reglas_personal
        )
        if _re.regla_existe(params_fin_lic):
            lic_puras = get_dias_licencia_pura(nombre)
            for d in range(dias_del_bloque - 1):
                # Si hoy está de licencia pero mañana NO lo está
                if d in lic_puras and (d+1) not in lic_puras:
                    # Debe trabajar en algún turno el día d+1
                    vars_manana = []
                    es_f_sig = ((d+1 + offset_dia) % 7) >= 5 or (d+1 in feriados)
                    tipo_dia_sig = "Finde_Feriado" if es_f_sig else "Semana"
                    for t in demanda_turnos.get(tipo_dia_sig, {}).keys():
                        if (nombre, d+1, t) in turnos:
                            vars_manana.append(turnos[(nombre, d+1, t)])
                    
                    if vars_manana:
                        modelo.Add(sum(vars_manana) >= 1)

    # 11. MÍNIMO DE HORAS POR MES CALENDARIO (Hard Limit)
    for index, persona in df_personal.iterrows():
        nombre = persona['Nombre']
        params_min_horas_cal = _re.resolver_parametros_regla(
            'MIN_HORAS_MES_CALENDARIO', nombre, FECHA_INICIO, 
            reglas_servicio, reglas_personal, ajustes_reglas_personal
        )
        if _re.regla_existe(params_min_horas_cal):
            min_h_total_objetivo = params_min_horas_cal.get('min_horas', 120) if isinstance(params_min_horas_cal, dict) else 120
            
            meses_en_bloque = {}
            for d in range(dias_del_bloque):
                m_key = (fecha_inicio_dt + timedelta(days=d)).strftime("%Y-%m")
                meses_en_bloque.setdefault(m_key, []).append(d)
                
            dias_bloqueados_p = get_dias_bloqueados(nombre)
            
            for m_key, dias_m in meses_en_bloque.items():
                vars_horas_m = []
                for d in dias_m:
                    es_f = ((d + offset_dia) % 7) >= 5 or d in feriados
                    tipo_dia_h = "Finde_Feriado" if es_f else "Semana"
                    for t in demanda_turnos.get(tipo_dia_h, {}).keys():
                        if (nombre, d, t) in turnos:
                            t_info = metadata_turnos.get(t)
                            h_turno = t_info["horas"] if t_info else 6
                            vars_horas_m.append(turnos[(nombre, d, t)] * h_turno)
                
                # Horas de licencia pro-rata (igual que en Rule 9)
                dias_lic_m = [d for d in dias_m if d in dias_bloqueados_p]
                val_dia = 144.0 / dias_del_bloque
                horas_licencia_m = int(val_dia * len(dias_lic_m) + 0.5)
                
                # Mínimo pro-rata para este tramo del mes
                min_pro_rata = int((min_h_total_objetivo / dias_del_bloque) * len(dias_m) + 0.5)
                
                # Restricción: Efectivas + Licencia >= Mínimo
                if vars_horas_m:
                    modelo.Add(sum(vars_horas_m) + horas_licencia_m >= min_pro_rata)
                        
