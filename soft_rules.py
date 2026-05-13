from datetime import date, timedelta
from data import FECHA_INICIO
import db as _db

def _get_licencias(): return _db.LAR, _db.LPP

def aplicar_reglas_blandas(modelo, turnos, df_personal, demanda_turnos, dias_del_bloque, feriados, offset_dia, num_semanas, servicio_id=1, flr_tracker=None, historial_semana_previa=None):
    # Cargar el motor de reglas desde la BD
    reglas_servicio = _db.cargar_reglas_servicio(servicio_id)
    reglas_personal = _db.cargar_reglas_personal(servicio_id)
    from data import FECHA_FIN
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
    max_ratio_finde_mes = modelo.NewIntVar(0, 1000, 'max_ratio_finde_mes')
    min_ratio_finde_mes = modelo.NewIntVar(0, 1000, 'min_ratio_finde_mes')
    
    max_ratio_finde_anual = modelo.NewIntVar(0, 1000, 'max_ratio_finde_anual')
    min_ratio_finde_anual = modelo.NewIntVar(0, 1000, 'min_ratio_finde_anual')

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
    puntos_transicion_semana = []
    semanas_seg_totales = []
    
    mapa_dias = {"Lunes": 0, "Martes": 1, "Miercoles": 2, "Jueves": 3, "Viernes": 4, "Sabado": 5, "Domingo": 6}

    fecha_inicio_dt = date.fromisoformat(FECHA_INICIO)
    
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
    
    max_ratio_finde_mes_cal = {m: modelo.NewIntVar(0, 1000, f'max_ratio_finde_mes_cal_{m}') for m in meses_calendario}
    min_ratio_finde_mes_cal = {m: modelo.NewIntVar(0, 1000, f'min_ratio_finde_mes_cal_{m}') for m in meses_calendario}

    def get_dias_bloqueados_soft(nombre):
        bloqueados = set()
        for licencias in _get_licencias():
            for (ini_str, fin_str) in licencias.get(nombre, []):
                ini = date.fromisoformat(ini_str)
                fin = date.fromisoformat(fin_str)
                for d in range(dias_del_bloque):
                    if ini <= fecha_inicio_dt + timedelta(days=d) <= fin:
                        bloqueados.add(d)
        return bloqueados

    for index, persona in df_personal.iterrows():
        nombre = persona['Nombre']
        rol = persona['Rol']
        dias_bloqueados_persona = get_dias_bloqueados_soft(nombre)
        horas_mes = []
        semanas_seg_persona = []
        
        # Contadores de tipos de semana para equidad
        semanas_M_persona = []
        semanas_T_persona = []
        semanas_TN_persona = []
        semanas_N_persona = []
        
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
            is_M = modelo.NewBoolVar(f'is_M_{nombre}_{sem_id}')
            is_T = modelo.NewBoolVar(f'is_T_{nombre}_{sem_id}')
            is_TN = modelo.NewBoolVar(f'is_TN_{nombre}_{sem_id}')
            is_N = modelo.NewBoolVar(f'is_N_{nombre}_{sem_id}')
            
            # --- Integrar historial para consistencia con el mes anterior ---
            if historial_semana_previa and nombre in historial_semana_previa:
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
                    modelo.AddImplication(turnos[(nombre, d, 'M')], is_M)
                    tiene_turnos_semana = True
                if (nombre, d, 'T') in turnos:
                    modelo.AddImplication(turnos[(nombre, d, 'T')], is_T)
                    tiene_turnos_semana = True
                if (nombre, d, 'TN') in turnos:
                    modelo.AddImplication(turnos[(nombre, d, 'TN')], is_TN)
                    tiene_turnos_semana = True
                if (nombre, d, 'N') in turnos:
                    modelo.AddImplication(turnos[(nombre, d, 'N')], is_N)
                    tiene_turnos_semana = True
                if (nombre, d, 'MT') in turnos:
                    modelo.Add(is_M + is_T >= 1).OnlyEnforceIf(turnos[(nombre, d, 'MT')])
                    tiene_turnos_semana = True
                if (nombre, d, 'TNN') in turnos:
                    modelo.Add(is_TN + is_N >= 1).OnlyEnforceIf(turnos[(nombre, d, 'TNN')])
                    tiene_turnos_semana = True
                    
            if tiene_turnos_semana:
                sum_is = modelo.NewIntVar(0, 4, f'sum_is_{nombre}_{sem_id}')
                modelo.Add(sum_is == is_M + is_T + is_TN + is_N)
                
                mix_penalty = modelo.NewIntVar(0, 3, f'mix_penalty_{nombre}_{sem_id}')
                modelo.Add(mix_penalty >= sum_is - 1)
                modelo.Add(mix_penalty >= 0)
                
                puntos_mix_horario.append(mix_penalty)
                
                semanas_M_persona.append(is_M)
                semanas_T_persona.append(is_T)
                semanas_TN_persona.append(is_TN)
                semanas_N_persona.append(is_N)

            # --- NUEVA LÓGICA: Consistencia entre el fin de esta semana y el inicio de la siguiente ---
            proxima_semana_key = (lunes_semana_dt + timedelta(days=7)).isoformat()
            if proxima_semana_key in dias_por_semana_calendario:
                dias_prox_sem = dias_por_semana_calendario[proxima_semana_key]
                if dias_semana_actual and dias_prox_sem:
                    ultimo_d = dias_semana_actual[-1]
                    primer_d_prox = dias_prox_sem[0]
                    # Solo penalizamos si el cambio es entre el Domingo y el Lunes
                    if (ultimo_d + offset_dia) % 7 == 6 and (primer_d_prox + offset_dia) % 7 == 0:
                        # Si trabajó un turno el domingo, preferimos que el lunes siga en el mismo "ritmo"
                        # Para simplificar, usamos las variables is_M, is_T, etc. de ambas semanas
                        prox_sem_id = proxima_semana_key.replace("-", "_")
                        is_M_prox = modelo.NewBoolVar(f'is_M_{nombre}_{prox_sem_id}')
                        is_T_prox = modelo.NewBoolVar(f'is_T_{nombre}_{prox_sem_id}')
                        is_TN_prox = modelo.NewBoolVar(f'is_TN_{nombre}_{prox_sem_id}')
                        is_N_prox = modelo.NewBoolVar(f'is_N_{nombre}_{prox_sem_id}')
                        
                        # Penalizamos si (is_M y no is_M_prox) o viceversa, etc.
                        # Pero solo si trabajaron en AMBAS semanas.
                        cambio_turno = modelo.NewBoolVar(f'cambio_turno_sem_{nombre}_{sem_id}')
                        # Si (is_M != is_M_prox) -> cambio
                        # Usamos una lógica simplificada: si is_M es 1, queremos que is_M_prox sea 1.
                        # Si is_M es 1 e is_M_prox es 0 -> penalización.
                        m_cambia = modelo.NewBoolVar(f'm_cambia_{nombre}_{sem_id}')
                        modelo.Add(is_M - is_M_prox <= m_cambia)
                        modelo.Add(is_M_prox - is_M <= m_cambia)
                        
                        t_cambia = modelo.NewBoolVar(f't_cambia_{nombre}_{sem_id}')
                        modelo.Add(is_T - is_T_prox <= t_cambia)
                        modelo.Add(is_T_prox - is_T <= t_cambia)

                        tn_cambia = modelo.NewBoolVar(f'tn_cambia_{nombre}_{sem_id}')
                        modelo.Add(is_TN - is_TN_prox <= tn_cambia)
                        modelo.Add(is_TN_prox - is_TN <= tn_cambia)

                        n_cambia = modelo.NewBoolVar(f'n_cambia_{nombre}_{sem_id}')
                        modelo.Add(is_N - is_N_prox <= n_cambia)
                        modelo.Add(is_N_prox - is_N <= n_cambia)

                        # Si ALGUNO cambia, sumamos a puntos de transición
                        # Usamos un peso menor que el mix horario para permitir rotación semanal si es necesario por equidad
                        puntos_transicion_semana.extend([m_cambia, t_cambia, tn_cambia, n_cambia])

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
                params_inconsistencia = rule_engine.resolver_parametros_regla('PESO_INCONSISTENCIA', nombre, FECHA_INICIO, reglas_servicio, reglas_personal, ajustes_personal)
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
            params_combo = rule_engine.resolver_parametros_regla('BONUS_COMBO_FINDE', nombre, FECHA_INICIO, reglas_servicio, reglas_personal, ajustes_personal)
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
                        h = 12 if (es_finde or t.startswith("Noche")) else 6
                        horas_mes.append(turnos[(nombre, d, t)] * h)
                        horas_por_mes_cal[mes_d_key].append(turnos[(nombre, d, t)] * h)

        # --- NIVELACIÓN POR RATIO TRABAJADOS / HÁBILES ---
        f_trab_prev = persona.get('Findes_Semanas_Previos', 0)
        f_hab_prev  = persona.get('Findes_Habiles_Previos', 10)
        
        # 1. Ratio Mensual (Solo bloque actual)
        f_trab_mes = sum(findes_trabajados_actual) if findes_trabajados_actual else 0
        f_hab_mes = findes_habiles_actual
        
        ratio_finde_mes = modelo.NewIntVar(0, 1000, f'ratio_finde_mes_{nombre}')
        if f_hab_mes > 0:
            if isinstance(f_trab_mes, int) and f_trab_mes == 0:
                modelo.Add(ratio_finde_mes == 0)
            else:
                modelo.Add(ratio_finde_mes * f_hab_mes <= f_trab_mes * 1000)
                modelo.Add(ratio_finde_mes * f_hab_mes > (f_trab_mes * 1000) - f_hab_mes)
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
                ratio_m = modelo.NewIntVar(0, 1000, f'ratio_finde_mes_cal_{m}_{nombre}')
                
                if f_hab_m > 0:
                    if isinstance(f_trab_m, int) and f_trab_m == 0:
                        modelo.Add(ratio_m == 0)
                    else:
                        modelo.Add(ratio_m * f_hab_m <= f_trab_m * 1000)
                        modelo.Add(ratio_m * f_hab_m > (f_trab_m * 1000) - f_hab_m)
                else:
                    modelo.Add(ratio_m == 0)
                    
                modelo.Add(ratio_m <= max_ratio_finde_mes_cal[m])
                modelo.Add(ratio_m >= min_ratio_finde_mes_cal[m])
            
        # 2. Ratio Anual (Histórico + Actual)
        f_trab_total = f_trab_prev + f_trab_mes
        f_hab_total  = f_hab_prev + f_hab_mes
        
        ratio_finde_anual = modelo.NewIntVar(0, 1000, f'ratio_finde_anual_{nombre}')
        modelo.Add(ratio_finde_anual * f_hab_total <= f_trab_total * 1000)
        modelo.Add(ratio_finde_anual * f_hab_total > (f_trab_total * 1000) - f_hab_total)
        
        params_findes_anual = rule_engine.resolver_parametros_regla(
            'PESO_EQUIDAD_FINDES_ANUAL', nombre, FECHA_INICIO, 
            reglas_servicio, reglas_personal, ajustes_personal
        )
        if not rule_engine.regla_suspendida(params_findes_anual):
            modelo.Add(ratio_finde_anual <= max_ratio_finde_anual)
            modelo.Add(ratio_finde_anual >= min_ratio_finde_anual)

        total_mes = sum(horas_mes)
        total_anual_proyectado = persona.get('Horas_Anuales_Previas', 0) + total_mes

        # Regla de mínimo mensual escalada
        tiene_licencia = len(dias_bloqueados_persona) > 0
        if not tiene_licencia:
            modelo.Add(total_mes >= min_horas_periodo)

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
            total_seg_proyectado = persona.get('Seguimientos_Previos', 0) + total_seg_mes
            
            modelo.Add(total_seg_proyectado <= max_seg)
            modelo.Add(total_seg_proyectado >= min_seg)

        # --- TURNOS PREFERENCIALES ---
        params_preferencias = rule_engine.resolver_parametros_regla('TURNOS_PREFERENCIALES', nombre, FECHA_INICIO, reglas_servicio, reglas_personal, ajustes_personal)
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
        if not rule_engine.regla_suspendida(params_flr):
            cantidad_requerida = params_flr.get('cantidad', 1) if isinstance(params_flr, dict) else 1
            flr_vars_persona_pref = []
            flr_vars_persona_alt = []
            
            for d in range(dias_del_bloque):
                dia_semana = (d + offset_dia) % 7
                es_sabado = (dia_semana == 5)
                es_jueves = (dia_semana == 3)
                
                if es_sabado or es_jueves:
                    turnos_en_bloque = []
                    for delta in range(4):
                        dia_eval = d + delta
                        if dia_eval < dias_del_bloque and dia_eval not in dias_bloqueados_persona:
                            es_f_e = ((dia_eval + offset_dia) % 7) >= 5 or dia_eval in feriados
                            tipo_dia_e = "Finde_Feriado" if es_f_e else "Semana"
                            for t in demanda_turnos.get(tipo_dia_e, {}).keys():
                                if (nombre, dia_eval, t) in turnos:
                                    turnos_en_bloque.append(turnos[(nombre, dia_eval, t)])
                    
                    if turnos_en_bloque:
                        tipo_str = "pref" if es_sabado else "alt"
                        tiene_flr = modelo.NewBoolVar(f'flr_{tipo_str}_{nombre}_d{d}')
                        modelo.Add(sum(turnos_en_bloque) == 0).OnlyEnforceIf(tiene_flr)
                        
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
                penalizaciones_flr.append(incumple_flr * 10000)
                
                # Penalización media por usar el alternativo (para preferir el Sábado)
                if flr_vars_persona_alt:
                    penalizaciones_flr.append(sum(flr_vars_persona_alt) * 3000)
            else:
                if cantidad_requerida > 0:
                    print(f"⚠️ [WARNING] {nombre} no tiene opciones de FLR (Sab o Jue) en este bloque debido a licencias/fechas.")

    # Lógica de Fines de Semana Largos y Equidad de Turnos
    max_fl3 = modelo.NewIntVar(0, 50, 'max_fl3')
    min_fl3 = modelo.NewIntVar(0, 50, 'min_fl3')
    max_fl4 = modelo.NewIntVar(0, 50, 'max_fl4')
    min_fl4 = modelo.NewIntVar(0, 50, 'min_fl4')
    
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

    for index, persona in df_personal.iterrows():
        nombre = persona['Nombre']
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

        total_fl3 = persona.get('Findes_Largos_3_Previos', 0) + sum(findes_3_trab_mes)
        total_fl4 = persona.get('Findes_Largos_4_Previos', 0) + sum(findes_4_trab_mes)
        
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
        params_fl3 = rule_engine.resolver_parametros_regla('PESO_EQUIDAD_FL3', nombre, FECHA_INICIO, reglas_servicio, reglas_personal, ajustes_personal)
        if not rule_engine.regla_suspendida(params_fl3):
            modelo.Add(total_fl3 <= max_fl3)
            modelo.Add(total_fl3 >= min_fl3)
            
        params_fl4 = rule_engine.resolver_parametros_regla('PESO_EQUIDAD_FL4', nombre, FECHA_INICIO, reglas_servicio, reglas_personal, ajustes_personal)
        if not rule_engine.regla_suspendida(params_fl4):
            modelo.Add(total_fl4 <= max_fl4)
            modelo.Add(total_fl4 >= min_fl4)

    brecha_mensual = modelo.NewIntVar(0, max_horas_limite, 'brecha_mensual')
    modelo.Add(brecha_mensual == max_horas_mes - min_horas_mes)
    brecha_anual = modelo.NewIntVar(0, max_anual_limite, 'brecha_anual')
    modelo.Add(brecha_anual == max_anual - min_anual)
    brecha_seg = modelo.NewIntVar(0, max_seg_limite, 'brecha_seg')
    modelo.Add(brecha_seg == max_seg - min_seg)
    brecha_ratio_finde_mes = modelo.NewIntVar(0, 1000, 'brecha_ratio_finde_mes')
    modelo.Add(brecha_ratio_finde_mes == max_ratio_finde_mes - min_ratio_finde_mes)
    
    brecha_ratio_finde_anual = modelo.NewIntVar(0, 1000, 'brecha_ratio_finde_anual')
    modelo.Add(brecha_ratio_finde_anual == max_ratio_finde_anual - min_ratio_finde_anual)

    # Brechas para meses calendario (Enfermería)
    brechas_mes_cal_vars = []
    brechas_finde_mes_cal_vars = []
    for m in meses_calendario:
        b_m = modelo.NewIntVar(0, max_horas_limite, f'brecha_mes_cal_{m}')
        modelo.Add(b_m == max_horas_mes_cal[m] - min_horas_mes_cal[m])
        brechas_mes_cal_vars.append(b_m)
        
        bf_m = modelo.NewIntVar(0, 1000, f'brecha_finde_mes_cal_{m}')
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
    peso_mix_horario = reglas_servicio.get('PESO_MIX_HORARIO', {}).get('peso', 500)
    peso_inconsistencia = reglas_servicio.get('PESO_INCONSISTENCIA', {}).get('peso', 100)

    # Construir función objetivo sumando las brechas calendario si están activas
    suma_brechas_mes_cal = sum(brechas_mes_cal_vars) * peso_mensual_cal if brechas_mes_cal_vars else 0
    suma_brechas_finde_mes_cal = sum(brechas_finde_mes_cal_vars) * peso_ratio_finde_mes_cal if brechas_finde_mes_cal_vars else 0

    # Penalización a turnos largos (MT, TNN)
    turnos_largos_vars = []
    for (nombre, d, t), var in turnos.items():
        if t in ['MT', 'TNN']:
            turnos_largos_vars.append(var)
    
    peso_turnos_largos = reglas_servicio.get('PESO_TURNOS_LARGOS', {}).get('peso', 50)
    penalizacion_turnos_largos = sum(turnos_largos_vars) * peso_turnos_largos if turnos_largos_vars else 0

    peso_equidad_tipo_turno = reglas_servicio.get('PESO_EQUIDAD_TIPO_TURNO', {}).get('peso', 150)
    brecha_equidad_turnos = (
        (max_sem_M - min_sem_M) + 
        (max_sem_T - min_sem_T) + 
        (max_sem_TN - min_sem_TN) + 
        (max_sem_N - min_sem_N)
    )

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
        (sum(puntos_transicion_semana) * 1000) +
        penalizacion_turnos_largos
    )
