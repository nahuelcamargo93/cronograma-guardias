from datetime import date, timedelta
from data import FECHA_INICIO, FECHA_FIN
try:
    from data import EVITAR_MEZCLA_SEMANAL_DURA
except ImportError:
    EVITAR_MEZCLA_SEMANAL_DURA = True

try:
    from data import PESO_MEZCLA_SEMANAL_SOFT
except ImportError:
    PESO_MEZCLA_SEMANAL_SOFT = 50000

try:
    from data import ROTACION_MENSUAL_DURA
except ImportError:
    ROTACION_MENSUAL_DURA = True

try:
    from data import PESO_ROTACION_MENSUAL_SOFT
except ImportError:
    PESO_ROTACION_MENSUAL_SOFT = 50000

import database as _db

def _get_licencias(): return _db.LAR, _db.LPP, _db.LM, _db.CM

def aplicar_reglas_blandas(modelo, turnos, empleados, demanda_turnos, turnos_dict, dias_del_bloque, feriados, offset_dia, num_semanas, servicio_id=1, flr_tracker=None, historial_semana_previa=None, demanda_req=None, ajustes_demanda=None, vars_turno_sem=None):
    # Cargar el motor de reglas desde la BD
    reglas_servicio = _db.cargar_reglas_servicio(servicio_id)
    reglas_personal = _db.cargar_reglas_personal(servicio_id)
    ajustes_personal = _db.cargar_ajustes_reglas_personal(FECHA_INICIO, FECHA_FIN)
    import rule_engine
    
    penalizaciones_flr = []

    # Extraer límites base desde la BD
    limites_config = reglas_servicio.get('LIMITES_SOFT_RULES', {})
    if not isinstance(limites_config, dict) or 'SEMANAS_BASE' not in limites_config:
        raise ValueError(f"Falta configurar la regla LIMITES_SOFT_RULES para el servicio {servicio_id} en la BD.")

    SEMANAS_BASE = limites_config.get('SEMANAS_BASE')
    MIN_HORAS_BASE = limites_config.get('MIN_HORAS_BASE')
    MAX_HORAS_LIMITE_BASE = limites_config.get('MAX_HORAS_LIMITE_BASE', 200)
    MAX_ANUAL_LIMITE = limites_config.get('MAX_ANUAL_LIMITE', 5000)
    MAX_SEG_LIMITE_BASE = limites_config.get('MAX_SEG_LIMITE_BASE', 50)
    MAX_FINDES_LIMITE_BASE = limites_config.get('MAX_FINDES_LIMITE_BASE', 8)

    min_horas_periodo = round(MIN_HORAS_BASE * num_semanas / SEMANAS_BASE)
    max_horas_limite  = round(MAX_HORAS_LIMITE_BASE * num_semanas / SEMANAS_BASE)
    max_anual_limite  = MAX_ANUAL_LIMITE
    max_seg_limite    = round(MAX_SEG_LIMITE_BASE * num_semanas / SEMANAS_BASE)
    max_findes_limite = round(MAX_FINDES_LIMITE_BASE * num_semanas / SEMANAS_BASE)

    # Métrica: Índice de Carga de Fines de Semana (Ratio Trabajados / Hábiles)
    max_ratio_finde_mes = modelo.NewIntVar(0, 100, 'max_ratio_finde_mes')
    min_ratio_finde_mes = modelo.NewIntVar(0, 100, 'min_ratio_finde_mes')
    
    max_ratio_finde_anual = modelo.NewIntVar(0, 100, 'max_ratio_finde_anual')
    min_ratio_finde_anual = modelo.NewIntVar(0, 100, 'min_ratio_finde_anual')

    # Otros balances (Brecha por Bloque - Kinesiología)
    max_horas_mes = modelo.NewIntVar(0, max_horas_limite, 'max_horas_mes')
    min_horas_mes = modelo.NewIntVar(0, max_horas_limite, 'min_horas_mes')
    max_anual = modelo.NewIntVar(0, max_anual_limite, 'max_anual')
    min_anual = modelo.NewIntVar(0, max_anual_limite, 'min_anual')
    max_seg = modelo.NewIntVar(0, max_seg_limite, 'max_seg')
    min_seg = modelo.NewIntVar(0, max_seg_limite, 'min_seg')

    puntos_seguimiento = []
    puntos_combo_finde = []
    puntos_mix_horario = []
    puntos_inconsistencia = []
    puntos_preferencias = []
    semanas_seg_totales = []
    penalizaciones_ad_hoc = []
    puntos_objetivo_rotacion = []
    puntos_diversidad = []
    puntos_bonus = []
    global_vars_turno_sem = {}
    if vars_turno_sem is not None:
        global_vars_turno_sem.update(vars_turno_sem)
    
    mapa_dias = {"Lunes": 0, "Martes": 1, "Miercoles": 2, "Jueves": 3, "Viernes": 4, "Sabado": 5, "Domingo": 6}

    fecha_inicio_dt = date.fromisoformat(FECHA_INICIO)
    _aplicar_min_dia_especifico_mes_soft(modelo, turnos, empleados, turnos_dict, reglas_servicio, ajustes_personal, dias_del_bloque, fecha_inicio_dt, penalizaciones_ad_hoc, servicio_id)
    
    # Determinar los meses calendario involucrados en el bloque
    meses_calendario = set()
    for d in range(dias_del_bloque):
        fecha_d = fecha_inicio_dt + timedelta(days=d)
        mes_key = f"{fecha_d.year}-{fecha_d.month:02d}"
        meses_calendario.add(mes_key)
    meses_calendario = sorted(list(meses_calendario))

    # Pre-crear las variables max y min para cada mes calendario
    max_horas_mes_cal = {m: modelo.NewIntVar(0, max_horas_limite, f'max_horas_mes_cal_{m}') for m in meses_calendario}
    min_horas_mes_cal = {m: modelo.NewIntVar(0, max_horas_limite, f'min_horas_mes_cal_{m}') for m in meses_calendario}
    
    max_ratio_finde_mes_cal = {m: modelo.NewIntVar(0, 100, f'max_ratio_finde_mes_cal_{m}') for m in meses_calendario}
    min_ratio_finde_mes_cal = {m: modelo.NewIntVar(0, 100, f'min_ratio_finde_mes_cal_{m}') for m in meses_calendario}


    # Lógica de Fines de Semana Largos y Equidad de Turnos
    # Sin tope máximo fijo: los FL3/FL4 se acumulan a lo largo de los años.
    # OR-Tools ajusta el dominio real durante el presolve.
    # Usamos un límite amplio para que nunca cause inviabilidad.
    _max_fl3_hist = max((e.findes_largos_3_previos for e in empleados), default=0)
    _max_fl4_hist = max((e.findes_largos_4_previos for e in empleados), default=0)
    _fl3_limite = _max_fl3_hist + num_semanas + 10   # historial real + máximo teórico del bloque
    _fl4_limite = _max_fl4_hist + num_semanas + 10
    max_fl3 = modelo.NewIntVar(0, max(_fl3_limite, 1), 'max_fl3')
    min_fl3 = modelo.NewIntVar(0, max(_fl3_limite, 1), 'min_fl3')
    max_fl4 = modelo.NewIntVar(0, max(_fl4_limite, 1), 'max_fl4')
    min_fl4 = modelo.NewIntVar(0, max(_fl4_limite, 1), 'min_fl4')
    
    max_sem_M = modelo.NewIntVar(0, 10, 'max_sem_M')
    min_sem_M = modelo.NewIntVar(0, 10, 'min_sem_M')
    max_sem_T = modelo.NewIntVar(0, 10, 'max_sem_T')
    min_sem_T = modelo.NewIntVar(0, 10, 'min_sem_T')
    max_sem_TN = modelo.NewIntVar(0, 10, 'max_sem_TN')
    min_sem_TN = modelo.NewIntVar(0, 10, 'min_sem_TN')
    max_sem_N = modelo.NewIntVar(0, 10, 'max_sem_N')
    min_sem_N = modelo.NewIntVar(0, 10, 'min_sem_N')

    es_descanso = [(((d + offset_dia) % 7) >= 5 or d in feriados) for d in range(dias_del_bloque)]
    bloques = []
    bloque_actual = []
    for d in range(dias_del_bloque):
        if es_descanso[d]: bloque_actual.append(d)
        else:
            if len(bloque_actual) >= 3: bloques.append(bloque_actual)
            bloque_actual = []
    if len(bloque_actual) >= 3: bloques.append(bloque_actual)

    for emp in empleados:
        nombre = emp.nombre
        rol = emp.rol
        dias_bloqueados_persona = emp.dias_licencia
        
        # Penalización dinámica por turno (vía DB)
        params_penal_turno = rule_engine.resolver_parametros_regla('PENALIZACION_TURNO', nombre, FECHA_INICIO, reglas_servicio, emp.reglas, ajustes_personal)
        if rule_engine.regla_existe(params_penal_turno):
            items = params_penal_turno if isinstance(params_penal_turno, list) else [params_penal_turno]
            for item in items:
                t_a_penalizar = item.get('turno')
                peso = item.get('peso', 100)
                solo_semana = item.get('solo_semana', False)
                solo_finde = item.get('solo_finde', False)
                dias_validos = item.get('dias')
                if t_a_penalizar:
                    for d in range(dias_del_bloque):
                        if (nombre, d, t_a_penalizar) in turnos:
                            aplica = True
                            es_f = ((d + offset_dia) % 7) >= 5 or d in feriados
                            if solo_semana and es_f:
                                aplica = False
                            if solo_finde and not es_f:
                                aplica = False
                            if dias_validos is not None:
                                dia_sem = (d + offset_dia) % 7
                                if dia_sem not in dias_validos:
                                    aplica = False
                            if aplica:
                                print(f"DEBUG: Penalizando {nombre} dia {d} turno {t_a_penalizar} peso {peso} es_f={es_f}")
                                penalizaciones_ad_hoc.append(turnos[(nombre, d, t_a_penalizar)] * peso)

        horas_mes = []
        semanas_seg_persona = []
        
        # Contadores de tipos de semana para equidad
        semanas_M_persona = []
        semanas_T_persona = []
        semanas_TN_persona = []
        semanas_N_persona = []
        semanas_trabajadas_persona = []
        
        findes_trabajados_actual = []

        # --- AGRUPAR DÍAS POR SEMANA CALENDARIO (Lunes-Domingo) ---
        dias_por_semana_calendario = {}
        for d in range(dias_del_bloque):
            fecha_d = fecha_inicio_dt + timedelta(days=d)
            lunes_semana = fecha_d - timedelta(days=fecha_d.weekday())
            sem_key = lunes_semana.isoformat()
            dias_por_semana_calendario.setdefault(sem_key, []).append(d)

        findes_habiles_actual = 0
        
        horas_por_mes_cal = {m: [] for m in meses_calendario}
        findes_trab_por_mes_cal = {m: [] for m in meses_calendario}
        findes_hab_por_mes_cal = {m: 0 for m in meses_calendario}

        # Pre-crear variables de tipo de turno por semana para esta persona
        vars_turno_sem_emp = {}
        for s_key in dias_por_semana_calendario.keys():
            if vars_turno_sem is not None and (nombre, s_key) in vars_turno_sem:
                vars_turno_sem_emp[s_key] = vars_turno_sem[(nombre, s_key)]
            else:
                s_id = s_key.replace("-", "_")
                v_dict = {
                    'M': modelo.NewBoolVar(f'is_M_{nombre}_{s_id}'),
                    'T': modelo.NewBoolVar(f'is_T_{nombre}_{s_id}'),
                    'TN': modelo.NewBoolVar(f'is_TN_{nombre}_{s_id}'),
                    'N': modelo.NewBoolVar(f'is_N_{nombre}_{s_id}')
                }
                vars_turno_sem_emp[s_key] = v_dict
                global_vars_turno_sem[(nombre, s_key)] = v_dict

        for sem_key, dias_semana_actual in dias_por_semana_calendario.items():
            sem_id = sem_key.replace("-", "_")
            lunes_semana_dt = date.fromisoformat(sem_key)
            lunes_a_viernes = [d for d in dias_semana_actual if ((d + offset_dia) % 7) < 5]
            
            # --- LÓGICA DE FINES DE SEMANA HÁBILES Y TRABAJADOS ---
            sabados = [d for d in dias_semana_actual if ((d + offset_dia) % 7) == 5]
            domingos = [d for d in dias_semana_actual if ((d + offset_dia) % 7) == 6]
            
            if sabados and domingos:
                s = sabados[0]
                dom = domingos[0]
                fecha_s = fecha_inicio_dt + timedelta(days=s)
                mes_s_key = f"{fecha_s.year}-{fecha_s.month:02d}"
                
                # Un fin de semana es hábil si no hay licencia ni sábado ni domingo
                if s not in dias_bloqueados_persona and dom not in dias_bloqueados_persona:
                    findes_habiles_actual += 1
                    findes_hab_por_mes_cal[mes_s_key] += 1
                
                # Variable binaria: ¿trabaja este fin de semana? (Cualquier turno en S o D)
                traba_este_finde = modelo.NewBoolVar(f'traba_finde_{nombre}_{sem_id}')
                t_f_names = demanda_turnos.get("Finde_Feriado", {}).keys()
                turnos_finde_v = [turnos[(nombre, s, t)] for t in t_f_names if (nombre, s, t) in turnos] + \
                                 [turnos[(nombre, dom, t)] for t in t_f_names if (nombre, dom, t) in turnos]
                
                if turnos_finde_v:
                    modelo.AddMaxEquality(traba_este_finde, turnos_finde_v)
                    findes_trabajados_actual.append(traba_este_finde)
                    findes_trab_por_mes_cal[mes_s_key].append(traba_este_finde)

            # --- LÓGICA DE CONSISTENCIA DE TURNOS EN LA SEMANA (MIX HORARIO) ---
            is_M = vars_turno_sem_emp[sem_key]['M']
            is_T = vars_turno_sem_emp[sem_key]['T']
            is_TN = vars_turno_sem_emp[sem_key]['TN']
            is_N = vars_turno_sem_emp[sem_key]['N']
            
            # --- Integrar historial para consistencia con el mes anterior ---
            if vars_turno_sem is None and historial_semana_previa and nombre in historial_semana_previa:
                for h_guardia in historial_semana_previa[nombre]:
                    h_fecha_str = h_guardia.get('fecha')
                    if h_fecha_str:
                        h_fecha = date.fromisoformat(h_fecha_str)
                        # Si el día del historial pertenece a esta misma semana Lunes-Domingo
                        if lunes_semana_dt <= h_fecha < lunes_semana_dt + timedelta(days=7):
                            h_t = h_guardia['turno']
                            if h_t == 'M': modelo.Add(is_M == 1)
                            elif h_t == 'T': modelo.Add(is_T == 1)
                            elif h_t == 'TN': modelo.Add(is_TN == 1)
                            elif h_t == 'N': modelo.Add(is_N == 1)
                            elif h_t in ['MT', 'M_UCO', 'M_UTI']: modelo.Add(is_M + is_T >= 1)
                            elif h_t in ['TNN']: modelo.Add(is_TN + is_N >= 1)

            tiene_turnos_semana = False
            for d in dias_semana_actual:
                if (nombre, d, 'M') in turnos:
                    if vars_turno_sem is None:
                        modelo.AddImplication(turnos[(nombre, d, 'M')], is_M)
                    tiene_turnos_semana = True
                if (nombre, d, 'T') in turnos:
                    if vars_turno_sem is None:
                        modelo.AddImplication(turnos[(nombre, d, 'T')], is_T)
                    tiene_turnos_semana = True
                if (nombre, d, 'TN') in turnos:
                    if vars_turno_sem is None:
                        modelo.AddImplication(turnos[(nombre, d, 'TN')], is_TN)
                    tiene_turnos_semana = True
                if (nombre, d, 'N') in turnos:
                    if vars_turno_sem is None:
                        modelo.AddImplication(turnos[(nombre, d, 'N')], is_N)
                    tiene_turnos_semana = True
                if (nombre, d, 'MT') in turnos:
                    if vars_turno_sem is None:
                        modelo.Add(is_M + is_T >= 1).OnlyEnforceIf(turnos[(nombre, d, 'MT')])
                    tiene_turnos_semana = True
                if (nombre, d, 'TNN') in turnos:
                    if vars_turno_sem is None:
                        modelo.Add(is_TN + is_N >= 1).OnlyEnforceIf(turnos[(nombre, d, 'TNN')])
                    tiene_turnos_semana = True
                    
            if tiene_turnos_semana:
                if vars_turno_sem is None:
                    # Acotación superior estricta para evitar trampas del solver durante licencias/francos
                    vars_M_semana = [turnos[(nombre, d, 'M')] for d in dias_semana_actual if (nombre, d, 'M') in turnos]
                    vars_T_semana = [turnos[(nombre, d, 'T')] for d in dias_semana_actual if (nombre, d, 'T') in turnos]
                    vars_TN_semana = [turnos[(nombre, d, 'TN')] for d in dias_semana_actual if (nombre, d, 'TN') in turnos]
                    vars_N_semana = [turnos[(nombre, d, 'N')] for d in dias_semana_actual if (nombre, d, 'N') in turnos]
                    vars_MT_semana = [turnos[(nombre, d, 'MT')] for d in dias_semana_actual if (nombre, d, 'MT') in turnos]
                    vars_TNN_semana = [turnos[(nombre, d, 'TNN')] for d in dias_semana_actual if (nombre, d, 'TNN') in turnos]

                    modelo.Add(is_M <= sum(vars_M_semana) + sum(vars_MT_semana))
                    modelo.Add(is_T <= sum(vars_T_semana) + sum(vars_MT_semana))
                    modelo.Add(is_TN <= sum(vars_TN_semana) + sum(vars_TNN_semana))
                    modelo.Add(is_N <= sum(vars_N_semana) + sum(vars_TNN_semana))

                    # REGLA DURA: Una semana solo puede ser de un tipo (M, T, TN o N)
                    if EVITAR_MEZCLA_SEMANAL_DURA:
                        modelo.Add(is_M + is_T + is_TN + is_N <= 1)
                
                # Regla Blanda: Penalizar mezcla de turnos en la misma semana (solo si no es dura)
                if not EVITAR_MEZCLA_SEMANAL_DURA:
                    mix_semana = modelo.NewBoolVar(f'mix_semana_{nombre}_{sem_id}')
                    # Si la suma es >= 2, mix_semana debe ser 1 (máxima suma teórica es 4, por eso el factor 3)
                    modelo.Add(is_M + is_T + is_TN + is_N - 1 <= mix_semana * 3)
                    puntos_mix_horario.append(mix_semana)
                
                semanas_M_persona.append(is_M)
                semanas_T_persona.append(is_T)
                semanas_TN_persona.append(is_TN)
                semanas_N_persona.append(is_N)

                # Variable que indica si trabajó en esta semana
                trabaja_esta_semana = modelo.NewBoolVar(f'trabaja_semana_{nombre}_{sem_id}')
                modelo.AddMaxEquality(trabaja_esta_semana, [is_M, is_T, is_TN, is_N])
                semanas_trabajadas_persona.append(trabaja_esta_semana)

                        
                        




            # Puntos de seguimiento "blandos" (como en el original)
            turnos_a_evaluar = ["Mañana_UTI", "Mañana_UCO"] if rol in ["Jefe", "Coordinador"] else list(demanda_turnos.get("Semana", {}).keys())
            for t in turnos_a_evaluar:
                dias_trabajados = [turnos[(nombre, d, t)] for d in lunes_a_viernes if (nombre, d, t) in turnos]
                if dias_trabajados:
                    puntos_seguimiento.extend(dias_trabajados)

            # Consultar si esta persona puede aplicar para Semanas de Seguimiento
            params_seg_premio = rule_engine.resolver_parametros_regla(
                'BONUS_SEG_TOTAL', nombre, FECHA_INICIO, 
                reglas_servicio, reglas_personal, ajustes_personal
            )
            
            # Lógica de Semanas de Seguimiento Completas (>= 4 turnos)
            if not rule_engine.regla_suspendida(params_seg_premio):
                # Excluir días bloqueados por licencia
                lv_disponibles = [d for d in lunes_a_viernes if d not in dias_bloqueados_persona]
                m_norm = [turnos[(nombre, d, t)] for d in lv_disponibles for t in ["Mañana_UTI", "Mañana_UCO"] if (nombre, d, t) in turnos]
                t_norm = [turnos[(nombre, d, t)] for d in lv_disponibles for t in ["Tarde_UTI", "Tarde_UCO"] if (nombre, d, t) in turnos]
                
                cumple_ind = modelo.NewBoolVar(f'premio_seg_ind_{nombre}_{sem_id}')
                if m_norm and t_norm:
                    cumple_m = modelo.NewBoolVar(f'premio_seg_m_{nombre}_{sem_id}')
                    cumple_t = modelo.NewBoolVar(f'premio_seg_t_{nombre}_{sem_id}')
                    modelo.Add(sum(m_norm) >= 4).OnlyEnforceIf(cumple_m)
                    modelo.Add(sum(t_norm) >= 4).OnlyEnforceIf(cumple_t)
                    modelo.AddBoolOr([cumple_m, cumple_t]).OnlyEnforceIf(cumple_ind)
                    semanas_seg_persona.append(cumple_ind)

                # Consultar motor de reglas para Inconsistencia
                params_inconsistencia = rule_engine.resolver_parametros_regla('PESO_INCONSISTENCIA', nombre, FECHA_INICIO, reglas_servicio, emp.reglas, ajustes_personal)
                if not rule_engine.regla_suspendida(params_inconsistencia):
                    # Agrupar turnos en el mismo tipo
                    all_lv_vars = [turnos[(nombre, d, t)] for d in lunes_a_viernes for t in demanda_turnos.get("Semana", {}).keys() if (nombre, d, t) in turnos]
                    if all_lv_vars:
                        total_lv = modelo.NewIntVar(0, 5, f'total_lv_{nombre}_{sem_id}')
                        modelo.Add(total_lv == sum(all_lv_vars))
                        diffs_tipo = []
                        for t_tipo in ["Mañana_UTI", "Mañana_UCO", "Tarde_UTI", "Tarde_UCO"]:
                            vars_tipo = [turnos[(nombre, d, t_tipo)] for d in lunes_a_viernes if (nombre, d, t_tipo) in turnos]
                            if vars_tipo:
                                n_tipo = sum(vars_tipo)
                                diff = modelo.NewIntVar(0, 5, f'diff_{t_tipo}_{nombre}_{sem_id}')
                                modelo.Add(diff == total_lv - n_tipo)
                                diffs_tipo.append(diff)
                        if diffs_tipo:
                            inconsistencia = modelo.NewIntVar(0, 5, f'inc_{nombre}_{sem_id}')
                            modelo.AddMinEquality(inconsistencia, diffs_tipo)
                            puntos_inconsistencia.append(inconsistencia)

            # Consultar motor de reglas para Combos de fin de semana
            params_combo = rule_engine.resolver_parametros_regla('BONUS_COMBO_FINDE', nombre, FECHA_INICIO, reglas_servicio, emp.reglas, ajustes_personal)
            if not rule_engine.regla_suspendida(params_combo) and sabados and domingos:
                s = sabados[0]
                dom = domingos[0]
                for t_finde in demanda_turnos.get("Finde_Feriado", {}).keys():
                    if (nombre, s, t_finde) in turnos and (nombre, dom, t_finde) in turnos:
                        combo = modelo.NewBoolVar(f'combo_{nombre}_{sem_id}_{t_finde}')
                        modelo.AddMinEquality(combo, [turnos[(nombre, s, t_finde)], turnos[(nombre, dom, t_finde)]])
                        puntos_combo_finde.append(combo)

            for d in dias_semana_actual:
                es_finde = ((d + offset_dia) % 7) >= 5 or d in feriados
                tipo_dia_soft = "Finde_Feriado" if es_finde else "Semana"
                list_t = demanda_turnos.get(tipo_dia_soft, {}).keys()
                
                fecha_d = fecha_inicio_dt + timedelta(days=d)
                mes_d_key = f"{fecha_d.year}-{fecha_d.month:02d}"
                
                for t in list_t:
                    if (nombre, d, t) in turnos:
                        if t not in turnos_dict:
                            raise ValueError(f"El turno '{t}' no está configurado en la base de datos (tabla turnos_config).")
                        h = turnos_dict[t].horas
                        horas_mes.append(turnos[(nombre, d, t)] * h)
                        horas_por_mes_cal[mes_d_key].append(turnos[(nombre, d, t)] * h)

        # --- NIVELACIÓN POR RATIO TRABAJADOS / HÁBILES ---
        f_trab_prev = emp.findes_semanas_previos
        f_hab_prev  = emp.findes_habiles_previos
        
        # 1. Ratio Mensual (Solo bloque actual)
        f_trab_mes = sum(findes_trabajados_actual) if findes_trabajados_actual else 0
        f_hab_mes = findes_habiles_actual
        
        ratio_finde_mes = modelo.NewIntVar(0, 100, f'ratio_finde_mes_{nombre}')
        if f_hab_mes > 0:
            if isinstance(f_trab_mes, int) and f_trab_mes == 0:
                modelo.Add(ratio_finde_mes == 0)
            else:
                modelo.Add(ratio_finde_mes * f_hab_mes <= f_trab_mes * 100)
                modelo.Add(ratio_finde_mes * f_hab_mes > (f_trab_mes * 100) - f_hab_mes)
        else:
            modelo.Add(ratio_finde_mes == 0)
            
        params_findes_mes = rule_engine.resolver_parametros_regla(
            'PESO_EQUIDAD_FINDES_MENSUAL', nombre, FECHA_INICIO, 
            reglas_servicio, reglas_personal, ajustes_personal
        )
        if not rule_engine.regla_suspendida(params_findes_mes):
            modelo.Add(ratio_finde_mes <= max_ratio_finde_mes)
            modelo.Add(ratio_finde_mes >= min_ratio_finde_mes)
            
        # 1.5 Ratio Mensual Calendario (Enfermería)
        params_findes_mes_cal = rule_engine.resolver_parametros_regla(
            'PESO_EQUIDAD_FINDES_MENSUAL_CALENDARIO', nombre, FECHA_INICIO, 
            reglas_servicio, reglas_personal, ajustes_personal
        )
        if not rule_engine.regla_suspendida(params_findes_mes_cal):
            for m in meses_calendario:
                f_trab_m = sum(findes_trab_por_mes_cal[m]) if findes_trab_por_mes_cal[m] else 0
                f_hab_m = findes_hab_por_mes_cal[m]
                ratio_m = modelo.NewIntVar(0, 100, f'ratio_finde_mes_cal_{m}_{nombre}')
                
                if f_hab_m > 0:
                    if isinstance(f_trab_m, int) and f_trab_m == 0:
                        modelo.Add(ratio_m == 0)
                    else:
                        modelo.Add(ratio_m * f_hab_m <= f_trab_m * 100)
                        modelo.Add(ratio_m * f_hab_m > (f_trab_m * 100) - f_hab_m)
                    # Solo participar en la equidad global si hay fines de semana hábiles
                    # Si todos los fines tienen licencia, el ratio es 0 y no debe jalarse hacia arriba
                    modelo.Add(ratio_m <= max_ratio_finde_mes_cal[m])
                    modelo.Add(ratio_m >= min_ratio_finde_mes_cal[m])
                else:
                    # Sin fines hábiles en este mes: ratio es 0, excluir de equidad global
                    modelo.Add(ratio_m == 0)
            
        # 2. Ratio Anual (Histórico + Actual)
        f_trab_total = f_trab_prev + f_trab_mes
        f_hab_total  = f_hab_prev + f_hab_mes
        
        ratio_finde_anual = modelo.NewIntVar(0, 100, f'ratio_finde_anual_{nombre}')
        modelo.Add(ratio_finde_anual * f_hab_total <= f_trab_total * 100)
        modelo.Add(ratio_finde_anual * f_hab_total > (f_trab_total * 100) - f_hab_total)
        
        params_findes_anual = rule_engine.resolver_parametros_regla(
            'PESO_EQUIDAD_FINDES_ANUAL', nombre, FECHA_INICIO, 
            reglas_servicio, reglas_personal, ajustes_personal
        )
        if not rule_engine.regla_suspendida(params_findes_anual):
            modelo.Add(ratio_finde_anual <= max_ratio_finde_anual)
            modelo.Add(ratio_finde_anual >= min_ratio_finde_anual)

        total_mes = sum(horas_mes)
        total_anual_proyectado = emp.horas_anuales_previas + total_mes

        # Regla de mínimo mensual escalada
        # tiene_licencia = len(dias_bloqueados_persona) > 0
        # if not tiene_licencia:
        #    modelo.Add(total_mes >= min_horas_periodo)

        # Consultar motor de reglas para Brecha Mensual (Kinesiología)
        params_mes = rule_engine.resolver_parametros_regla(
            'PESO_BRECHA_MENSUAL', nombre, FECHA_INICIO, 
            reglas_servicio, reglas_personal, ajustes_personal
        )
        if not rule_engine.regla_suspendida(params_mes):
            modelo.Add(total_mes <= max_horas_mes)
            modelo.Add(total_mes >= min_horas_mes)
            
        # 2. Balances por Mes Calendario (Enfermería)
        for m in meses_calendario:
            # Días de este mes en el bloque
            dias_en_mes_m = [d for d in range(dias_del_bloque) if (fecha_inicio_dt + timedelta(days=d)).strftime("%Y-%m") == m]
            if not dias_en_mes_m: continue
            
            # Cálculo de horas de licencia pro-rata para este mes/bloque
            dias_lic_m = [d for d in dias_en_mes_m if d in dias_bloqueados_persona]
            # Usamos la misma base que el reporte (144 / dias_totales_bloque) * dias_licencia
            val_dia = 144.0 / dias_del_bloque
            horas_licencia_m = int(val_dia * len(dias_lic_m) + 0.5)
            
            # Total Horas = Efectivas + Licencia
            total_mes_m = sum(horas_por_mes_cal[m]) + horas_licencia_m
            
            # Equidad (Brecha Mensual Calendario)
            params_mes_cal = rule_engine.resolver_parametros_regla(
                'PESO_BRECHA_MENSUAL_CALENDARIO', nombre, FECHA_INICIO, 
                reglas_servicio, reglas_personal, ajustes_personal
            )
            if not rule_engine.regla_suspendida(params_mes_cal):
                modelo.Add(total_mes_m <= max_horas_mes_cal[m])
                modelo.Add(total_mes_m >= min_horas_mes_cal[m])
            
            # Límite Máximo (Movido a hard_rules.py para consistencia)
            pass
                
        # Consultar motor de reglas para Brecha Anual
        params_anual = rule_engine.resolver_parametros_regla(
            'PESO_BRECHA_ANUAL', nombre, FECHA_INICIO, 
            reglas_servicio, reglas_personal, ajustes_personal
        )
        if not rule_engine.regla_suspendida(params_anual):
            modelo.Add(total_anual_proyectado <= max_anual)
            modelo.Add(total_anual_proyectado >= min_anual)
        
        # Consultar si esta persona participa en la Brecha de Seguimiento
        params_brecha_seg = rule_engine.resolver_parametros_regla(
            'PESO_BRECHA_SEG', nombre, FECHA_INICIO, 
            reglas_servicio, reglas_personal, ajustes_personal
        )
        
        if not rule_engine.regla_suspendida(params_brecha_seg) and semanas_seg_persona:
            total_seg_mes = sum(semanas_seg_persona)
            semanas_seg_totales.extend(semanas_seg_persona)
            total_seg_proyectado = emp.seguimientos_previos + total_seg_mes
            
            modelo.Add(total_seg_proyectado <= max_seg)
            modelo.Add(total_seg_proyectado >= min_seg)

        # --- TURNOS PREFERENCIALES ---
        params_preferencias = rule_engine.resolver_parametros_regla('TURNOS_PREFERENCIALES', nombre, FECHA_INICIO, reglas_servicio, emp.reglas, ajustes_personal)
        if not rule_engine.regla_suspendida(params_preferencias) and isinstance(params_preferencias, list):
            for pref in params_preferencias:
                dia_objetivo = mapa_dias.get(pref['Dia'])
                turno_pref = pref['Turno'].replace(" ", "_")
                for d in range(dias_del_bloque):
                    if (d + offset_dia) % 7 == dia_objetivo and d not in dias_bloqueados_persona:
                        es_f = ((d + offset_dia) % 7) >= 5 or d in feriados
                        td_soft_p = "Finde_Feriado" if es_f else "Semana"
                        list_t = demanda_turnos.get(td_soft_p, {}).keys()
                        vars_pref = [turnos[(nombre, d, t)] for t in list_t 
                                     if (nombre, d, t) in turnos and (t == turno_pref or t.startswith(turno_pref + "_"))]
                        
                        if vars_pref:
                            cumple_pref = modelo.NewBoolVar(f'pref_{nombre}_d{d}_{turno_pref}')
                            modelo.Add(sum(vars_pref) == 1).OnlyEnforceIf(cumple_pref)
                            modelo.Add(sum(vars_pref) == 0).OnlyEnforceIf(cumple_pref.Not())
                            puntos_preferencias.append(cumple_pref)

        # --- FINDE LARGO REGLAMENTARIO (FLR) - Regla SOFT de alta prioridad ---
        params_flr = rule_engine.resolver_parametros_regla(
            'FINDE_LARGO_REGLAMENTARIO', nombre, FECHA_INICIO,
            reglas_servicio, reglas_personal, ajustes_personal
        )
        params_flr_estricto = rule_engine.resolver_parametros_regla(
            'FINDE_LARGO_REGLAMENTARIO_ESTRICTO', nombre, FECHA_INICIO,
            reglas_servicio, reglas_personal, ajustes_personal
        )

        active_flr_rule = None
        if rule_engine.regla_existe(params_flr) and not rule_engine.regla_suspendida(params_flr):
            active_flr_rule = ('normal', params_flr)
        elif rule_engine.regla_existe(params_flr_estricto) and not rule_engine.regla_suspendida(params_flr_estricto):
            active_flr_rule = ('estricto', params_flr_estricto)

        if active_flr_rule:
            tipo_regla, params = active_flr_rule
            cantidad_requerida = params.get('cantidad', 1) if isinstance(params, dict) else 1
            flr_vars_persona_pref = []
            flr_vars_persona_alt = []
            
            for d in range(dias_del_bloque):
                dia_semana = (d + offset_dia) % 7
                es_sabado = (dia_semana == 5)
                es_jueves = (dia_semana == 3)
                
                if es_sabado or es_jueves:
                    # Si la regla es ESTRICTA, los 4 días deben estar dentro del bloque
                    if tipo_regla == 'estricto' and d + 3 >= dias_del_bloque:
                        continue

                    # Verificar si los 4 días están disponibles (sin licencias que rompan el bloque)
                    dias_objetivo = [d, d+1, d+2, d+3]
                    turnos_en_bloque = []
                    for d_eval in dias_objetivo:
                        if d_eval < dias_del_bloque:
                            if d_eval in dias_bloqueados_persona:
                                turnos_en_bloque = []
                                break
                            es_f_e = ((d_eval + offset_dia) % 7) >= 5 or d_eval in feriados
                            tipo_dia_e = "Finde_Feriado" if es_f_e else "Semana"
                            for t in demanda_turnos.get(tipo_dia_e, {}).keys():
                                if (nombre, d_eval, t) in turnos:
                                    turnos_en_bloque.append(turnos[(nombre, d_eval, t)])
                        else:
                            if tipo_regla == 'estricto':
                                turnos_en_bloque = []
                                break
                    
                    if turnos_en_bloque:
                        tipo_str = "pref" if es_sabado else "alt"
                        tiene_flr = modelo.NewBoolVar(f'flr_{tipo_str}_{nombre}_d{d}')
                        modelo.Add(sum(turnos_en_bloque) == 0).OnlyEnforceIf(tiene_flr)
                        
                        # --- REGLA DURA ADYACENTE AL FLR: No francos antes ni después ---
                        # Si tiene FLR (4 días libres), DEBE trabajar el día anterior y posterior.
                        # Esto evita bloques de 5 o más días libres seguidos.

                        # Día anterior (d-1)
                        if d - 1 >= 0:
                            es_f_prev = ((d - 1 + offset_dia) % 7) >= 5 or (d - 1 in feriados)
                            tipo_dia_prev = "Finde_Feriado" if es_f_prev else "Semana"
                            vars_prev = [turnos[(nombre, d - 1, t)] for t in demanda_turnos.get(tipo_dia_prev, {}).keys() if (nombre, d - 1, t) in turnos]
                            if vars_prev:
                                # Obligar a trabajar (sum == 1) si tiene FLR
                                modelo.Add(sum(vars_prev) == 1).OnlyEnforceIf(tiene_flr)
                            else:
                                # Si no hay turnos posibles (licencia), no puede haber FLR aquí
                                modelo.Add(tiene_flr == 0)
                        
                        # Día posterior (d+4)
                        if d + 4 < dias_del_bloque:
                            es_f_post = ((d + 4 + offset_dia) % 7) >= 5 or (d + 4 in feriados)
                            tipo_dia_post = "Finde_Feriado" if es_f_post else "Semana"
                            vars_post = [turnos[(nombre, d + 4, t)] for t in demanda_turnos.get(tipo_dia_post, {}).keys() if (nombre, d + 4, t) in turnos]
                            if vars_post:
                                modelo.Add(sum(vars_post) == 1).OnlyEnforceIf(tiene_flr)
                            else:
                                modelo.Add(tiene_flr == 0)
                        
                        if es_sabado:
                            flr_vars_persona_pref.append(tiene_flr)
                        else:
                            flr_vars_persona_alt.append(tiene_flr)
                            
                        if flr_tracker is not None:
                            flr_tracker[(nombre, d)] = tiene_flr
            
            todas_vars_flr = flr_vars_persona_pref + flr_vars_persona_alt
            if todas_vars_flr:
                incumple_flr = modelo.NewIntVar(0, cantidad_requerida, f'incumple_flr_{nombre}')
                modelo.Add(sum(todas_vars_flr) + incumple_flr == cantidad_requerida)
                
                # Penalización altísima por no dar ningún FLR
                penalizaciones_flr.append(incumple_flr * 1000)
                
                # Penalización media por usar el alternativo (para preferir el Sábado)
                if flr_vars_persona_alt:
                    penalizaciones_flr.append(sum(flr_vars_persona_alt) * 3000)
            else:
                if cantidad_requerida > 0:
                    print(f"[WARNING] {nombre} no tiene opciones de FLR (Sab o Jue) en este bloque debido a licencias/fechas.")

        nombre = emp.nombre
        findes_3_trab_mes = []
        findes_4_trab_mes = []
        for bloque in bloques:
            t_f_names_fl = demanda_turnos.get("Finde_Feriado", {}).keys()
            turnos_en_bloque = [turnos[(nombre, d, t)] for d in bloque for t in t_f_names_fl if (nombre, d, t) in turnos]
            if turnos_en_bloque:
                trabaja_fl = modelo.NewBoolVar(f'trabaja_fl_{nombre}_b{bloque[0]}')
                modelo.AddMaxEquality(trabaja_fl, turnos_en_bloque)
                if len(bloque) == 3: findes_3_trab_mes.append(trabaja_fl)
                elif len(bloque) >= 4: findes_4_trab_mes.append(trabaja_fl)

        total_fl3 = emp.findes_largos_3_previos + sum(findes_3_trab_mes)
        total_fl4 = emp.findes_largos_4_previos + sum(findes_4_trab_mes)
        
        # Conexión con min/max de equidad de turnos
        if semanas_M_persona:
            modelo.Add(sum(semanas_M_persona) <= max_sem_M)
            modelo.Add(sum(semanas_M_persona) >= min_sem_M)
            modelo.Add(sum(semanas_T_persona) <= max_sem_T)
            modelo.Add(sum(semanas_T_persona) >= min_sem_T)
            modelo.Add(sum(semanas_TN_persona) <= max_sem_TN)
            modelo.Add(sum(semanas_TN_persona) >= min_sem_TN)
            modelo.Add(sum(semanas_N_persona) <= max_sem_N)
            modelo.Add(sum(semanas_N_persona) >= min_sem_N)
        
        # Consultar motor de reglas para Fines de Semana Largos
        params_fl3 = rule_engine.resolver_parametros_regla('PESO_EQUIDAD_FL3', nombre, FECHA_INICIO, reglas_servicio, emp.reglas, ajustes_personal)
        if not rule_engine.regla_suspendida(params_fl3):
            modelo.Add(total_fl3 <= max_fl3)
            modelo.Add(total_fl3 >= min_fl3)
            
        params_fl4 = rule_engine.resolver_parametros_regla('PESO_EQUIDAD_FL4', nombre, FECHA_INICIO, reglas_servicio, emp.reglas, ajustes_personal)
        if not rule_engine.regla_suspendida(params_fl4):
            modelo.Add(total_fl4 <= max_fl4)
            modelo.Add(total_fl4 >= min_fl4)
            
        # --- Objetivo de Rotación Mensual Individual ---
        params_rot = rule_engine.resolver_parametros_regla('OBJETIVO_ROTACION_MENSUAL', nombre, FECHA_INICIO, reglas_servicio, emp.reglas, ajustes_personal)
        if rule_engine.regla_existe(params_rot) and not rule_engine.regla_suspendida(params_rot):
            objetivos = params_rot.get('objetivos', {})
            peso_rot = params_rot.get('peso', 100)
            mapping = {'M': semanas_M_persona, 'T': semanas_T_persona, 'TN': semanas_TN_persona, 'N': semanas_N_persona}
            for t_code, sem_vars in mapping.items():
                if t_code in objetivos and sem_vars:
                    target = objetivos[t_code]
                    total_t = sum(sem_vars)
                    diff = modelo.NewIntVar(0, 10, f'diff_rot_{t_code}_{nombre}')
                    modelo.AddAbsEquality(diff, total_t - target)
                    puntos_objetivo_rotacion.append(diff * peso_rot)
                    
        # --- Penalización por Turno Ausente (Diversidad Semanal) / Rotación Mensual ---
        params_div = rule_engine.resolver_parametros_regla('PENALIZACION_TURNO_AUSENTE', nombre, FECHA_INICIO, reglas_servicio, emp.reglas, ajustes_personal)
        if rule_engine.regla_existe(params_div) and not rule_engine.regla_suspendida(params_div):
            mapping_div = {'M': semanas_M_persona, 'T': semanas_T_persona, 'TN': semanas_TN_persona, 'N': semanas_N_persona}
            
            # Crear variables de presencia de cada familia en el mes
            has_family = {}
            for t_code, sem_vars in mapping_div.items():
                if sem_vars:
                    has_f = modelo.NewBoolVar(f'has_family_{t_code}_{nombre}')
                    modelo.Add(sum(sem_vars) >= 1).OnlyEnforceIf(has_f)
                    modelo.Add(sum(sem_vars) == 0).OnlyEnforceIf(has_f.Not())
                    has_family[t_code] = has_f
            
            if ROTACION_MENSUAL_DURA:
                # Ya aplicado en hard_rules.py como regla dura, no hacer nada aquí.
                pass
            else:
                # Regla Blanda: Penalizar la ausencia de cada turno con el peso configurado
                peso_div = PESO_ROTACION_MENSUAL_SOFT
                for t_code, has_f in has_family.items():
                    puntos_diversidad.append(has_f.Not() * peso_div)

        # --- BONUS POR CARGA PERFECTA ---
        params_bonus = rule_engine.resolver_parametros_regla('BONUS_POR_CARGA_PERFECTA', nombre, FECHA_INICIO, reglas_servicio, emp.reglas, ajustes_personal)
        if rule_engine.regla_existe(params_bonus) and not rule_engine.regla_suspendida(params_bonus) and turnos_dict:
            min_h = params_bonus.get('min_h', 142)
            max_h = params_bonus.get('max_h', 146)
            bonus_val = params_bonus.get('bonus', 2000)
            
            meses_en_bloque = {}
            fecha_inicio_dt = date.fromisoformat(FECHA_INICIO)
            for d in range(dias_del_bloque):
                m_key = (fecha_inicio_dt + timedelta(days=d)).strftime("%Y-%m")
                meses_en_bloque.setdefault(m_key, []).append(d)
            
            for m_key, dias_m in meses_en_bloque.items():
                h_vars_m = []
                for d in dias_m:
                    es_f = ((d + offset_dia) % 7) >= 5 or d in feriados
                    tipo_dia_h = "Finde_Feriado" if es_f else "Semana"
                    for t in demanda_turnos.get(tipo_dia_h, {}).keys():
                        if (nombre, d, t) in turnos:
                            if t not in turnos_dict:
                                raise ValueError(f"El turno '{t}' no está configurado en la base de datos (tabla turnos_config).")
                            h_t = turnos_dict[t].horas
                            h_vars_m.append(turnos[(nombre, d, t)] * h_t)
                
                # Licencias pro-rata
                dias_lic_m = [d for d in dias_m if d in dias_bloqueados_persona]
                val_dia = 144.0 / dias_del_bloque
                h_lic_m = int(val_dia * len(dias_lic_m) + 0.5)
                
                total_h_mes_var = modelo.NewIntVar(0, 500, f'h_mes_{nombre}_{m_key}')
                modelo.Add(total_h_mes_var == sum(h_vars_m) + h_lic_m)
                
                b_perfect = modelo.NewBoolVar(f'b_perfect_{nombre}_{m_key}')
                modelo.Add(total_h_mes_var >= min_h).OnlyEnforceIf(b_perfect)
                modelo.Add(total_h_mes_var <= max_h).OnlyEnforceIf(b_perfect)
                
                puntos_bonus.append(b_perfect * bonus_val)

    brecha_mensual = modelo.NewIntVar(0, max_horas_limite, 'brecha_mensual')
    modelo.Add(brecha_mensual == max_horas_mes - min_horas_mes)
    brecha_anual = modelo.NewIntVar(0, max_anual_limite, 'brecha_anual')
    modelo.Add(brecha_anual == max_anual - min_anual)
    brecha_seg = modelo.NewIntVar(0, max_seg_limite, 'brecha_seg')
    modelo.Add(brecha_seg == max_seg - min_seg)
    brecha_ratio_finde_mes = modelo.NewIntVar(0, 100, 'brecha_ratio_finde_mes')
    modelo.Add(brecha_ratio_finde_mes == max_ratio_finde_mes - min_ratio_finde_mes)
    
    brecha_ratio_finde_anual = modelo.NewIntVar(0, 100, 'brecha_ratio_finde_anual')
    modelo.Add(brecha_ratio_finde_anual == max_ratio_finde_anual - min_ratio_finde_anual)

    # Brechas para meses calendario (Enfermería)
    brechas_mes_cal_vars = []
    brechas_finde_mes_cal_vars = []
    for m in meses_calendario:
        b_m = modelo.NewIntVar(0, max_horas_limite, f'brecha_mes_cal_{m}')
        modelo.Add(b_m == max_horas_mes_cal[m] - min_horas_mes_cal[m])
        brechas_mes_cal_vars.append(b_m)
        
        bf_m = modelo.NewIntVar(0, 100, f'brecha_finde_mes_cal_{m}')
        modelo.Add(bf_m == max_ratio_finde_mes_cal[m] - min_ratio_finde_mes_cal[m])
        brechas_finde_mes_cal_vars.append(bf_m)

    # Cargar pesos dinámicos desde la BD (con fallbacks a los valores originales)
    params_globales_findes_mes = reglas_servicio.get('PESO_EQUIDAD_FINDES_MENSUAL', {})
    peso_ratio_finde_mes = params_globales_findes_mes.get('peso', 500) if isinstance(params_globales_findes_mes, dict) else 500
    
    params_globales_findes_anual = reglas_servicio.get('PESO_EQUIDAD_FINDES_ANUAL', {})
    peso_ratio_finde_anual = params_globales_findes_anual.get('peso', 500) if isinstance(params_globales_findes_anual, dict) else 500
    peso_anual = reglas_servicio.get('PESO_BRECHA_ANUAL', {}).get('peso', 100)
    peso_mensual = reglas_servicio.get('PESO_BRECHA_MENSUAL', {}).get('peso', 50)
    
    # Nuevos pesos calendario
    peso_mensual_cal = reglas_servicio.get('PESO_BRECHA_MENSUAL_CALENDARIO', {}).get('peso', 50)
    peso_ratio_finde_mes_cal = reglas_servicio.get('PESO_EQUIDAD_FINDES_MENSUAL_CALENDARIO', {}).get('peso', 500)
    
    peso_seg = reglas_servicio.get('PESO_BRECHA_SEG', {}).get('peso', 100)
    peso_fl3 = reglas_servicio.get('PESO_EQUIDAD_FL3', {}).get('peso', 500)
    peso_fl4 = reglas_servicio.get('PESO_EQUIDAD_FL4', {}).get('peso', 500)
    peso_seg_totales = reglas_servicio.get('BONUS_SEG_TOTAL', {}).get('peso', 150)
    peso_puntos_seg = reglas_servicio.get('BONUS_SEG_PUNTOS', {}).get('peso', 5)
    peso_combo_finde = reglas_servicio.get('BONUS_COMBO_FINDE', {}).get('peso', 15)
    peso_preferencias = reglas_servicio.get('BONUS_PREFERENCIAS', {}).get('peso', 300)
    if not EVITAR_MEZCLA_SEMANAL_DURA:
        peso_mix_horario = PESO_MEZCLA_SEMANAL_SOFT
    else:
        peso_mix_horario = reglas_servicio.get('PESO_MIX_HORARIO', {}).get('peso', 500)
    peso_inconsistencia = reglas_servicio.get('PESO_INCONSISTENCIA', {}).get('peso', 100)

    # Construir función objetivo sumando las brechas calendario si están activas
    suma_brechas_mes_cal = sum(brechas_mes_cal_vars) * peso_mensual_cal if brechas_mes_cal_vars else 0
    suma_brechas_finde_mes_cal = sum(brechas_finde_mes_cal_vars) * peso_ratio_finde_mes_cal if brechas_finde_mes_cal_vars else 0


    peso_equidad_tipo_turno = reglas_servicio.get('PESO_EQUIDAD_TIPO_TURNO', {}).get('peso', 150)
    brecha_equidad_turnos = (
        (max_sem_M - min_sem_M) + 
        (max_sem_T - min_sem_T) + 
        (max_sem_TN - min_sem_TN) + 
        (max_sem_N - min_sem_N)
    )

    # Regla: PESO_BRECHA_DIARIA_PERSONAL (Brecha por turno a lo largo del bloque + Déficit de cobertura)
    params_brecha_diaria = reglas_servicio.get('PESO_BRECHA_DIARIA_PERSONAL', {})
    if rule_engine.regla_existe(params_brecha_diaria) and not rule_engine.regla_suspendida(params_brecha_diaria):
        peso_brecha = params_brecha_diaria.get('peso_brecha', 100)
        peso_cobertura = params_brecha_diaria.get('peso_cobertura', 10)
        
        # Identificar todos los turnos del servicio
        todos_turnos = list(turnos_dict.keys())
        
        # 1. Minimizar brecha diaria por cada turno específico
        for t_nombre in todos_turnos:
            # Sumar las asignaciones a este turno específico para cada día
            totales_dias_t = []
            for d in range(dias_del_bloque):
                vars_dia_t = []
                for emp in empleados:
                    if (emp.nombre, d, t_nombre) in turnos:
                        vars_dia_t.append(turnos[(emp.nombre, d, t_nombre)])
                if vars_dia_t:
                    totales_dias_t.append(sum(vars_dia_t))
            
            if totales_dias_t:
                max_dia_t = modelo.NewIntVar(0, len(empleados), f'max_dia_t_{t_nombre}')
                min_dia_t = modelo.NewIntVar(0, len(empleados), f'min_dia_t_{t_nombre}')
                
                for total_d in totales_dias_t:
                    modelo.Add(max_dia_t >= total_d)
                    modelo.Add(min_dia_t <= total_d)
                
                brecha_t = modelo.NewIntVar(0, len(empleados), f'brecha_diaria_t_{t_nombre}')
                modelo.Add(brecha_t == max_dia_t - min_dia_t)
                
                penalizaciones_ad_hoc.append(brecha_t * peso_brecha)
        
        # 2. Minimizar déficit de cobertura (acercar cantidad a cantidad_max)
        if demanda_req:
            from utils import time_to_float
            for d in range(dias_del_bloque):
                es_f = ((d + offset_dia) % 7) >= 5 or d in feriados
                tipo_dia = "Finde_Feriado" if es_f else "Semana"
                fecha_actual_iso = (fecha_inicio_dt + timedelta(days=d)).isoformat()
                dia_semana_actual = (d + offset_dia) % 7
                
                demandas_por_ventana = {}
                for demanda in demanda_req.get(tipo_dia, []):
                    key = (demanda["hora_inicio"], demanda["hora_fin"])
                    demandas_por_ventana.setdefault(key, []).append(demanda)
                    
                for (h_start, h_end), window_demands in demandas_por_ventana.items():
                    d_h_start = time_to_float(h_start)
                    d_h_end = time_to_float(h_end)
                    d_abs_start = d * 24 + d_h_start
                    if d_h_end <= d_h_start and not (d_h_start == 0 and d_h_end == 0):
                        d_abs_end = (d + 1) * 24 + d_h_end
                    elif d_h_end == 0 and d_h_start > 0:
                        d_abs_end = (d + 1) * 24
                    else:
                        d_abs_end = d * 24 + d_h_end
                        
                    for dem in window_demands:
                        c_max = dem.get("cantidad_max")
                        if c_max is None or c_max <= 0:
                            continue
                            
                        # Buscar si hay ajuste de demanda
                        aj_o = None
                        if ajustes_demanda:
                            for (fi, ff), cambios in ajustes_demanda.items():
                                if fi <= fecha_actual_iso <= ff:
                                    for adj in cambios:
                                        if adj["demanda_config_id"] == dem["id"]:
                                            aj_o = adj
                                            break
                        if aj_o:
                            if aj_o["dias_override"]:
                                dias_validos = [int(x) for x in aj_o["dias_override"].split(",")]
                                if dia_semana_actual not in dias_validos and d not in feriados:
                                    c_max = 0
                                else:
                                    c_max = aj_o.get("cantidad_max")
                            else:
                                c_max = aj_o.get("cantidad_max")
                                
                        if c_max is None or c_max <= 0:
                            continue
                            
                        # Construir pool de variables normales que cubren esta ventana
                        pool_normales = []
                        for emp in empleados:
                            if d in emp.dias_licencia:
                                continue
                                
                            # Cargar si es extra
                            fecha_bloque = (fecha_inicio_dt + timedelta(days=d)).strftime("%Y-%m-%d")
                            params_extra = rule_engine.resolver_parametros_regla('PERSONAL_EXTRA_FUERA_MINIMO', emp.nombre, fecha_bloque, reglas_servicio, emp.reglas, ajustes_personal)
                            es_extra = False
                            if rule_engine.regla_existe(params_extra) and isinstance(params_extra, dict):
                                nombres_extra_resueltos = params_extra.get('nombres', [])
                                if emp.nombre in nombres_extra_resueltos:
                                    es_extra = True
                                    
                            if es_extra:
                                continue
                                
                            for t_nombre, t_info in turnos_dict.items():
                                if t_info.puesto_nombre != dem["puesto"]:
                                    continue
                                if (emp.nombre, d, t_nombre) in turnos:
                                    ts_abs = d * 24 + time_to_float(t_info.hora_inicio)
                                    te_abs = ts_abs + t_info.horas
                                    if ts_abs <= d_abs_start + 0.01 and te_abs >= d_abs_end - 0.01:
                                        pool_normales.append(turnos[(emp.nombre, d, t_nombre)])
                                        
                        if pool_normales:
                            # El déficit es max(0, c_max - sum(pool_normales))
                            # NOTA: No usar == porque sum(pool) puede superar c_max => valor negativo => INFEASIBLE
                            deficit_var = modelo.NewIntVar(0, c_max, f'deficit_{dem["id"]}_d{d}')
                            modelo.Add(deficit_var >= c_max - sum(pool_normales))
                            penalizaciones_ad_hoc.append(deficit_var * peso_cobertura)

    # Penalización por cobertura de Planta por parte de residentes (Priorización por año de residencia)
    if servicio_id == 3:
        for emp in empleados:
            if emp.rol == 'Residente':
                # Obtener año de residencia de emp.categoria
                try:
                    year = int(emp.categoria)
                except (ValueError, TypeError):
                    year = 4
                
                # Definir penalidad según el año
                if year == 4:
                    pen_value = 2000
                elif year == 3:
                    pen_value = 5000
                elif year == 2:
                    pen_value = 50000
                elif year == 1:
                    pen_value = 500000
                else:
                    pen_value = 500000
                
                # Buscar asignaciones de Planta
                for d in range(dias_del_bloque):
                    for t in turnos_dict.keys():
                        t_info = turnos_dict.get(t)
                        if t_info and t_info.puesto_nombre == 'Planta':
                            if (emp.nombre, d, t) in turnos:
                                penalizaciones_ad_hoc.append(turnos[(emp.nombre, d, t)] * pen_value)

    modelo.Minimize(
        (brecha_ratio_finde_mes * peso_ratio_finde_mes) + 
        (brecha_ratio_finde_anual * peso_ratio_finde_anual) +
        (brecha_anual * peso_anual) +
        (brecha_mensual * peso_mensual) +
        suma_brechas_mes_cal +
        suma_brechas_finde_mes_cal +
        (brecha_seg * peso_seg) +
        ((max_fl3 - min_fl3) * peso_fl3) + 
        ((max_fl4 - min_fl4) * peso_fl4) +
        (brecha_equidad_turnos * peso_equidad_tipo_turno) +
        sum(penalizaciones_flr) -
        (sum(semanas_seg_totales) * peso_seg_totales) - 
        (sum(puntos_seguimiento) * peso_puntos_seg) - 
        (sum(puntos_combo_finde) * peso_combo_finde) - 
        (sum(puntos_preferencias) * peso_preferencias) +
        (sum(puntos_mix_horario) * peso_mix_horario) +
        (sum(puntos_inconsistencia) * peso_inconsistencia) +
        sum(penalizaciones_ad_hoc) +
        sum(puntos_objetivo_rotacion) +
        sum(puntos_diversidad) - 
        sum(puntos_bonus)
    )
    return global_vars_turno_sem

def _aplicar_min_dia_especifico_mes_soft(modelo, turnos_vars, empleados, turnos_dict, reglas_servicio, ajustes_reglas, dias_del_bloque, fecha_inicio_dt, penalizaciones_ad_hoc, servicio_id=1):
    mapa_dias = {
        'lunes': 0, 'martes': 1, 'miercoles': 2, 'jueves': 3, 'viernes': 4, 'sabado': 5, 'domingo': 6,
        'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3, 'friday': 4, 'saturday': 5, 'sunday': 6
    }
    
    import rule_engine as _re
    from data import FERIADOS
    
    # Pre-calcular feriados como índices para agrupar fines de semana
    feriados_indices = []
    for f_str in FERIADOS:
        f_dt = date.fromisoformat(f_str)
        delta = (f_dt - fecha_inicio_dt).days
        if 0 <= delta < dias_del_bloque:
            feriados_indices.append(delta)
            
    offset_dia = fecha_inicio_dt.weekday()
    findes = {}
    for d_f in range(dias_del_bloque):
        fecha_df = fecha_inicio_dt + timedelta(days=d_f)
        dia_semana_f = (d_f + offset_dia) % 7
        es_finde_f = (dia_semana_f >= 5) or (d_f in feriados_indices)
        if es_finde_f:
            lunes_f = (fecha_df - timedelta(days=fecha_df.weekday())).isoformat()
            findes.setdefault(lunes_f, []).append(d_f)
            
    for emp in empleados:
        # Resolver parámetros para el bloque (usando la fecha de inicio)
        fecha_ini_str = fecha_inicio_dt.isoformat()
        params_min = _re.resolver_parametros_regla(
            'MIN_DIA_ESPECIFICO_MES', emp.nombre, fecha_ini_str,
            reglas_servicio, emp.reglas, ajustes_reglas
        )
        params_exacto = _re.resolver_parametros_regla(
            'EXACTO_DIA_ESPECIFICO_MES', emp.nombre, fecha_ini_str,
            reglas_servicio, emp.reglas, ajustes_reglas
        )
        
        has_min = _re.regla_existe(params_min) and not _re.regla_suspendida(params_min)
        has_exacto = _re.regla_existe(params_exacto) and not _re.regla_suspendida(params_exacto)
        
        # Si MIN_DIA_ESPECIFICO_MES está suspendida para este empleado, heredamos la suspensión a EXACTO_DIA_ESPECIFICO_MES
        if has_exacto and params_min is not None and _re.regla_suspendida(params_min):
            has_exacto = False
            
        if not has_min and not has_exacto:
            continue
            
        is_exact = has_exacto
        params = params_exacto if has_exacto else params_min
            
        dia_conf = params.get('dia_semana', 4)
        if isinstance(dia_conf, str):
            dia_str = dia_conf.lower().replace('é', 'e').replace('á', 'a').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
            dia_semana_target = mapa_dias.get(dia_str, 4)
        else:
            dia_semana_target = int(dia_conf)
            
        min_dias_req = params.get('exacto_dias', params.get('min_dias', 1))
        
        # Calcular semanas disponibles
        k = sum(1 for lunes_f, dias_f in findes.items() if any(d_f not in emp.dias_licencia for d_f in dias_f))
        
        if params.get('dinamico_licencias', False):
            # Regla de cálculo dinámico para los viernes (4)
            if dia_semana_target == 4:
                if k >= 4:
                    target_dias = 1
                elif k == 3:
                    target_dias = 0
                elif k == 2:
                    target_dias = 1
                else:
                    target_dias = 0
            else:
                target_dias = min_dias_req
        else:
            target_dias = min_dias_req
                
        if target_dias == 0 and not is_exact:
            continue
        
        vars_dia = []
        for d in range(dias_del_bloque):
            fecha_d = fecha_inicio_dt + timedelta(days=d)
            if fecha_d.weekday() == dia_semana_target:
                # Exclusiones justas y matemáticamente seguras (como la regla original)
                if d in emp.dias_licencia:
                    continue
                fecha_d_str = fecha_d.isoformat()
                p_franco = _re.resolver_parametros_regla('FRANCO_FORZADO', emp.nombre, fecha_d_str, reglas_servicio, emp.reglas, ajustes_reglas)
                if _re.regla_existe(p_franco) and not _re.regla_suspendida(p_franco):
                    continue
                    
                v_este_dia = modelo.NewBoolVar(f'traba_dia_esp_soft_{emp.nombre}_{dia_semana_target}_{d}')
                pool_d = []
                for t in turnos_dict.keys():
                    if (emp.nombre, d, t) in turnos_vars:
                        pool_d.append(turnos_vars[(emp.nombre, d, t)])
                        
                if pool_d:
                    modelo.AddMaxEquality(v_este_dia, pool_d)
                    vars_dia.append(v_este_dia)
                    
        if vars_dia:
            target_real = min(target_dias, len(vars_dia))
            if is_exact:
                violation_under = modelo.NewIntVar(0, target_real, f'viol_under_dia_esp_{emp.nombre}_{dia_semana_target}')
                violation_over = modelo.NewIntVar(0, len(vars_dia), f'viol_over_dia_esp_{emp.nombre}_{dia_semana_target}')
                modelo.Add(sum(vars_dia) + violation_under - violation_over == target_real)
                
                violation = modelo.NewIntVar(0, len(vars_dia) + target_real, f'viol_dia_esp_{emp.nombre}_{dia_semana_target}')
                modelo.Add(violation == violation_under + violation_over)
                penalizaciones_ad_hoc.append(violation * 100000)
            else:
                violation = modelo.NewIntVar(0, target_real, f'viol_dia_esp_{emp.nombre}_{dia_semana_target}')
                modelo.Add(violation >= target_real - sum(vars_dia))
                # Penalidad muy alta: 1.000.000 (un millón) por cada viernes no cubierto!
                penalizaciones_ad_hoc.append(violation * 100000)


