from datetime import date, timedelta
from logic_helpers import TURNOS_SEMANA, TURNOS_FINDE
import db as _db

def _get_licencias(): return _db.LAR, _db.LPP, _db.LM, _db.CM

def aplicar_reglas_blandas(modelo, turnos, df_personal, dias_del_bloque, feriados, offset_dia, num_semanas, fecha_inicio, turnos_config=None, reglas_soft=None):
    reglas_soft = reglas_soft or {}
    def get_weight(key, default):
        try:
            return int(reglas_soft.get(key, default))
        except (ValueError, TypeError):
            return default

    # Semanas de referencia base (el sistema fue calibrado para 4 semanas)
    SEMANAS_BASE = 4
    fecha_inicio_dt = date.fromisoformat(fecha_inicio)

    # Mínimo de horas por período escalado: 108 hs era el mínimo para 4 semanas (~27hs/semana)
    MIN_HORAS_BASE = 108
    min_horas_periodo = round(MIN_HORAS_BASE * num_semanas / SEMANAS_BASE)

    # Límites superiores de IntVar escalados para que el solver tenga espacio suficiente
    max_horas_limite  = round(200 * num_semanas / SEMANAS_BASE)
    max_anual_limite  = 5000  # El acumulado anual no cambia su cota superior
    max_seg_limite    = round(50 * num_semanas / SEMANAS_BASE)
    max_findes_limite = round(8  * num_semanas / SEMANAS_BASE)

    # Métrica: Índice de Carga de Fines de Semana (Ratio Trabajados / Hábiles)
    max_ratio_finde = modelo.NewIntVar(0, 1000, 'max_ratio_finde')
    min_ratio_finde = modelo.NewIntVar(0, 1000, 'min_ratio_finde')

    # Otros balances
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
    
    mapa_dias = {"Lunes": 0, "Martes": 1, "Miercoles": 2, "Jueves": 3, "Viernes": 4, "Sabado": 5, "Domingo": 6}

    fecha_inicio_dt = date.fromisoformat(FECHA_INICIO)

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
        
        findes_trabajados_actual = []
        findes_habiles_actual = 0

        for semana in range(dias_del_bloque // 7):
            dias_semana_actual = range(semana * 7, (semana + 1) * 7)
            lunes_a_viernes = [d for d in dias_semana_actual if ((d + offset_dia) % 7) < 5]
            
            # --- LÓGICA DE FINES DE SEMANA HÁBILES Y TRABAJADOS ---
            sabados = [d for d in dias_semana_actual if ((d + offset_dia) % 7) == 5]
            domingos = [d for d in dias_semana_actual if ((d + offset_dia) % 7) == 6]
            
            if sabados and domingos:
                s = sabados[0]
                dom = domingos[0]
                
                # Un fin de semana es hábil si no hay licencia ni sábado ni domingo
                if s not in dias_bloqueados_persona and dom not in dias_bloqueados_persona:
                    findes_habiles_actual += 1
                
                # Variable binaria: ¿trabaja este fin de semana? (Cualquier turno en S o D)
                traba_este_finde = modelo.NewBoolVar(f'traba_finde_{nombre}_sem{semana}')
                turnos_finde = [turnos[(nombre, s, t)] for t in TURNOS_FINDE if (nombre, s, t) in turnos] + \
                               [turnos[(nombre, dom, t)] for t in TURNOS_FINDE if (nombre, dom, t) in turnos]
                
                if turnos_finde:
                    modelo.AddMaxEquality(traba_este_finde, turnos_finde)
                    findes_trabajados_actual.append(traba_este_finde)

            # Puntos de seguimiento "blandos" (como en el original)
            turnos_a_evaluar = ["Mañana_UTI", "Mañana_UCO"] if rol in ["Jefe", "Coordinador"] else TURNOS_SEMANA
            for t in turnos_a_evaluar:
                dias_trabajados = [turnos[(nombre, d, t)] for d in lunes_a_viernes if (nombre, d, t) in turnos]
                if dias_trabajados:
                    puntos_seguimiento.extend(dias_trabajados)

            # Lógica de Semanas de Seguimiento Completas para Rotativos (>= 4 turnos)
            if rol not in ["Jefe", "Coordinador"]:
                # Excluir días bloqueados por licencia
                lv_disponibles = [d for d in lunes_a_viernes if d not in dias_bloqueados_persona]
                m_norm = [turnos[(nombre, d, t)] for d in lv_disponibles for t in ["Mañana_UTI", "Mañana_UCO"] if (nombre, d, t) in turnos]
                t_norm = [turnos[(nombre, d, t)] for d in lv_disponibles for t in ["Tarde_UTI", "Tarde_UCO"] if (nombre, d, t) in turnos]
                
                cumple_ind = modelo.NewBoolVar(f'premio_seg_ind_{nombre}_sem{semana}')
                if m_norm and t_norm:
                    cumple_m = modelo.NewBoolVar(f'premio_seg_m_{nombre}_sem{semana}')
                    cumple_t = modelo.NewBoolVar(f'premio_seg_t_{nombre}_sem{semana}')
                    modelo.Add(sum(m_norm) >= 4).OnlyEnforceIf(cumple_m)
                    modelo.Add(sum(t_norm) >= 4).OnlyEnforceIf(cumple_t)
                    modelo.AddBoolOr([cumple_m, cumple_t]).OnlyEnforceIf(cumple_ind)
                    semanas_seg_persona.append(cumple_ind)
                
                # Consistencia horaria
                traba_m = modelo.NewBoolVar(f'traba_m_{nombre}_sem{semana}')
                traba_t = modelo.NewBoolVar(f'traba_t_{nombre}_sem{semana}')
                vars_m = [turnos[(nombre, d, t)] for d in lunes_a_viernes for t in ["Mañana_UTI", "Mañana_UCO", "Mañana_especial"] if (nombre, d, t) in turnos]
                vars_t = [turnos[(nombre, d, t)] for d in lunes_a_viernes for t in ["Tarde_UTI", "Tarde_UCO", "Tarde_especial"] if (nombre, d, t) in turnos]
                if vars_m: modelo.AddMaxEquality(traba_m, vars_m)
                else: modelo.Add(traba_m == 0)
                if vars_t: modelo.AddMaxEquality(traba_t, vars_t)
                else: modelo.Add(traba_t == 0)
                mix_mt = modelo.NewBoolVar(f'mix_mt_{nombre}_sem{semana}')
                modelo.AddMinEquality(mix_mt, [traba_m, traba_t])
                puntos_mix_horario.append(mix_mt)

                # Agrupar turnos en el mismo tipo
                all_lv_vars = [turnos[(nombre, d, t)] for d in lunes_a_viernes for t in TURNOS_SEMANA if (nombre, d, t) in turnos]
                if all_lv_vars:
                    total_lv = modelo.NewIntVar(0, 5, f'total_lv_{nombre}_sem{semana}')
                    modelo.Add(total_lv == sum(all_lv_vars))
                    diffs_tipo = []
                    for t_tipo in ["Mañana_UTI", "Mañana_UCO", "Tarde_UTI", "Tarde_UCO"]:
                        vars_tipo = [turnos[(nombre, d, t_tipo)] for d in lunes_a_viernes if (nombre, d, t_tipo) in turnos]
                        if vars_tipo:
                            n_tipo = sum(vars_tipo)
                            diff = modelo.NewIntVar(0, 5, f'diff_{t_tipo}_{nombre}_sem{semana}')
                            modelo.Add(diff == total_lv - n_tipo)
                            diffs_tipo.append(diff)
                    if diffs_tipo:
                        inconsistencia = modelo.NewIntVar(0, 5, f'inc_{nombre}_sem{semana}')
                        modelo.AddMinEquality(inconsistencia, diffs_tipo)
                        puntos_inconsistencia.append(inconsistencia)

            # Combos de fin de semana (mismo turno S y D)
            if sabados and domingos:
                s = sabados[0]
                dom = domingos[0]
                for t_finde in TURNOS_FINDE:
                    if (nombre, s, t_finde) in turnos and (nombre, dom, t_finde) in turnos:
                        combo = modelo.NewBoolVar(f'combo_{nombre}_sem{semana}_{t_finde}')
                        modelo.AddMinEquality(combo, [turnos[(nombre, s, t_finde)], turnos[(nombre, dom, t_finde)]])
                        puntos_combo_finde.append(combo)

            for d in range(semana * 7, (semana + 1) * 7):
                es_finde = ((d + offset_dia) % 7) >= 5 or d in feriados
                list_t = TURNOS_FINDE if es_finde else TURNOS_SEMANA
                for t in list_t:
                    if (nombre, d, t) in turnos:
                        h = turnos_config.get(t, 6) if turnos_config else (12 if (es_finde or t.startswith("Noche")) else 6)
                        horas_mes.append(turnos[(nombre, d, t)] * h)

        # --- NIVELACIÓN POR RATIO TRABAJADOS / HÁBILES ---
        f_trab_prev = persona.get('Findes_Semanas_Previos', 0)
        f_hab_prev  = persona.get('Findes_Habiles_Previos', 10)
        
        f_trab_total = f_trab_prev + sum(findes_trabajados_actual)
        f_hab_total  = f_hab_prev + findes_habiles_actual
        
        # Ratio * 1000 para trabajar con enteros (Nivelación aproximada)
        ratio_finde = modelo.NewIntVar(0, 1000, f'ratio_finde_{nombre}')
        # ratio_finde = (f_trab_total * 1000) // f_hab_total
        modelo.Add(ratio_finde * f_hab_total <= f_trab_total * 1000)
        modelo.Add(ratio_finde * f_hab_total > (f_trab_total * 1000) - f_hab_total)
        
        modelo.Add(ratio_finde <= max_ratio_finde)
        modelo.Add(ratio_finde >= min_ratio_finde)

        total_mes = sum(horas_mes)
        total_anual_proyectado = persona.get('Horas_Anuales_Previas', 0) + total_mes

        # Regla de mínimo mensual escalada
        tiene_licencia = len(dias_bloqueados_persona) > 0
        if not tiene_licencia:
            modelo.Add(total_mes >= min_horas_periodo)

        modelo.Add(total_mes <= max_horas_mes)
        modelo.Add(total_mes >= min_horas_mes)
        modelo.Add(total_anual_proyectado <= max_anual)
        modelo.Add(total_anual_proyectado >= min_anual)
        
        if rol not in ["Jefe", "Coordinador"] and semanas_seg_persona:
            total_seg_mes = sum(semanas_seg_persona)
            semanas_seg_totales.extend(semanas_seg_persona)
            total_seg_proyectado = persona.get('Seguimientos_Previos', 0) + total_seg_mes
            modelo.Add(total_seg_proyectado <= max_seg)
            modelo.Add(total_seg_proyectado >= min_seg)

        # --- TURNOS PREFERENCIALES ---
        preferencias = persona.get('Turnos_Preferenciales', [])
        if isinstance(preferencias, list):
            for pref in preferencias:
                dia_objetivo = mapa_dias.get(pref['Dia'])
                turno_pref = pref['Turno'].replace(" ", "_")
                for d in range(dias_del_bloque):
                    if (d + offset_dia) % 7 == dia_objetivo and d not in dias_bloqueados_persona:
                        es_f = ((d + offset_dia) % 7) >= 5 or d in feriados
                        list_t = TURNOS_FINDE if es_f else TURNOS_SEMANA
                        vars_pref = [turnos[(nombre, d, t)] for t in list_t 
                                     if (nombre, d, t) in turnos and (t == turno_pref or t.startswith(turno_pref + "_"))]
                        
                        if vars_pref:
                            cumple_pref = modelo.NewBoolVar(f'pref_{nombre}_d{d}_{turno_pref}')
                            modelo.Add(sum(vars_pref) == 1).OnlyEnforceIf(cumple_pref)
                            modelo.Add(sum(vars_pref) == 0).OnlyEnforceIf(cumple_pref.Not())
                            puntos_preferencias.append(cumple_pref)

    # Lógica de Fines de Semana Largos
    max_fl3 = modelo.NewIntVar(0, 50, 'max_fl3')
    min_fl3 = modelo.NewIntVar(0, 50, 'min_fl3')
    max_fl4 = modelo.NewIntVar(0, 50, 'max_fl4')
    min_fl4 = modelo.NewIntVar(0, 50, 'min_fl4')

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
            turnos_en_bloque = [turnos[(nombre, d, t)] for d in bloque for t in TURNOS_FINDE if (nombre, d, t) in turnos]
            if turnos_en_bloque:
                trabaja_fl = modelo.NewBoolVar(f'trabaja_fl_{nombre}_b{bloque[0]}')
                modelo.AddMaxEquality(trabaja_fl, turnos_en_bloque)
                if len(bloque) == 3: findes_3_trab_mes.append(trabaja_fl)
                elif len(bloque) >= 4: findes_4_trab_mes.append(trabaja_fl)

        total_fl3 = persona.get('Findes_Largos_3_Previos', 0) + sum(findes_3_trab_mes)
        total_fl4 = persona.get('Findes_Largos_4_Previos', 0) + sum(findes_4_trab_mes)
        modelo.Add(total_fl3 <= max_fl3)
        modelo.Add(total_fl3 >= min_fl3)
        modelo.Add(total_fl4 <= max_fl4)
        modelo.Add(total_fl4 >= min_fl4)

    brecha_mensual = modelo.NewIntVar(0, max_horas_limite, 'brecha_mensual')
    modelo.Add(brecha_mensual == max_horas_mes - min_horas_mes)
    brecha_anual = modelo.NewIntVar(0, max_anual_limite, 'brecha_anual')
    modelo.Add(brecha_anual == max_anual - min_anual)
    brecha_seg = modelo.NewIntVar(0, max_seg_limite, 'brecha_seg')
    modelo.Add(brecha_seg == max_seg - min_seg)
    brecha_ratio_finde = modelo.NewIntVar(0, 1000, 'brecha_ratio_finde')
    modelo.Add(brecha_ratio_finde == max_ratio_finde - min_ratio_finde)

    # --- CONSTRUCCIÓN DEL OBJETIVO FINAL ---
    modelo.Minimize(
        brecha_ratio_finde     * get_weight('peso_balance_finde', 1000) +
        brecha_anual           * get_weight('peso_balance_anual', 100) +
        brecha_mensual         * get_weight('peso_balance_mensual', 50) +
        brecha_seg             * get_weight('peso_balance_seguimiento', 100) +
        (max_fl3 - min_fl3)    * get_weight('peso_balance_fl3', 500) +
        (max_fl4 - min_fl4)    * get_weight('peso_balance_fl4', 500) +
        sum(semanas_seg_totales) * -get_weight('peso_recompensa_seguimiento', 150) +
        sum(puntos_seguimiento) * -get_weight('peso_recompensa_dias_seguimiento', 5) +
        sum(puntos_combo_finde) * -get_weight('peso_recompensa_combo_finde', 15) +
        sum(puntos_preferencias) * -get_weight('peso_recompensa_preferencias', 300) +
        sum(puntos_mix_horario)  * get_weight('peso_penalizacion_mix_horario', 500) +
        sum(puntos_inconsistencia) * get_weight('peso_penalizacion_inconsistencia', 100)
    )
