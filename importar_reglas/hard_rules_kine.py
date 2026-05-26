from datetime import date, timedelta
from logic_helpers import TURNOS_SEMANA, TURNOS_FINDE
import db as _db

def _get_licencias(): return _db.LAR, _db.LPP, _db.LM, _db.CM

def aplicar_reglas_duras(modelo, turnos, df_personal, demanda_turnos, dias_del_bloque, feriados, offset_dia, num_semanas, fecha_inicio, turnos_config=None, reglas_hard=None):
    reglas_hard = reglas_hard or {}
    # Semanas de referencia base (originalmente el sistema fue calibrado para 4 semanas)
    SEMANAS_BASE = 4
    # 0. LAR / LPP: bloquear todos los turnos en días de licencia
    fecha_inicio_dt = date.fromisoformat(fecha_inicio)

    def get_dias_bloqueados(nombre):
        """Set de índices de día (0-based) en que la persona está de LAR o LPP."""
        bloqueados = set()
        for licencias in _get_licencias():
            for (ini_str, fin_str) in licencias.get(nombre, []):
                ini = date.fromisoformat(ini_str)
                fin = date.fromisoformat(fin_str)
                for d in range(dias_del_bloque):
                    if ini <= fecha_inicio_dt + timedelta(days=d) <= fin:
                        bloqueados.add(d)
        return bloqueados

    licencias_semanales = {}
    for index, persona in df_personal.iterrows():
        nombre = persona['Nombre']
        bloqueados = get_dias_bloqueados(nombre)
        for d in bloqueados:
            for t in TURNOS_SEMANA + TURNOS_FINDE:
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

    # 1. REGLA DINÁMICA: LÍMITES DE NOCHES Y TURNOS PROHIBIDOS
    for index, persona in df_personal.iterrows():
        nombre = persona['Nombre']
        noches_vble = [turnos[(nombre, d, "Noche")] for d in range(dias_del_bloque) if (nombre, d, "Noche") in turnos]
        if not persona.get('Puede_Noche', True):
            for n in noches_vble:
                modelo.Add(n == 0)
        elif noches_vble:
            # Escalar Max_Noches proporcionalmente al período
            max_noches_base = int(persona.get('Max_Noches', reglas_hard.get('max_noches_mensuales_base', 4)))
            max_noches_escalado = round(max_noches_base * num_semanas / SEMANAS_BASE)
            modelo.Add(sum(noches_vble) <= max_noches_escalado)
    
        prohibidos_lv = persona.get('Turnos_Prohibidos_LV', [])
        for d in range(dias_del_bloque):
            for t_prohibido in prohibidos_lv:
                if (nombre, d, t_prohibido) in turnos:
                    modelo.Add(turnos[(nombre, d, t_prohibido)] == 0)

    # 2. REGLA DINÁMICA: SEMANAS DE SEGUIMIENTO
    # Aplica a Jefes/Coordinadores Y a cualquier persona con seguimientos específicos (Mañana/Tarde)
    for index, persona in df_personal.iterrows():
        nombre = persona['Nombre']
        rol = persona.get('Rol')
        seguimientos = persona.get('Semanas_Seguimiento', {})

        # Determinar si esta persona necesita regla dura de seguimiento:
        # - Siempre: Jefes y Coordinadores
        # - También: cualquiera con seguimientos de tipo "Mañana" o "Tarde" explícitos
        tiene_seg_especificos = any(k.startswith("Mañana") or k.startswith("Tarde") for k in seguimientos)
        es_jefe_coord = rol in ["Jefe", "Coordinador"]

        if not es_jefe_coord and not tiene_seg_especificos:
            continue

        if seguimientos:
            # Calcular cuántas semanas candidatas tiene esta persona (con >= 4 días L-V libres)
            # Esto se necesita para detectar conflicto entre múltiples tipos de seguimiento
            tipos_activos = [t for t in seguimientos if not (t == "Indistinto" and not es_jefe_coord)]
            total_semanas_requeridas = sum(seguimientos[t] for t in tipos_activos)

            # Pre-calcular semanas candidatas una sola vez para esta persona
            bloqueados_persona = get_dias_bloqueados(nombre)
            dias_min_seguimiento = int(reglas_hard.get('dias_min_seguimiento', 4))
            semanas_indices = [
                sem for sem in range(dias_del_bloque // 7)
                if len([d for d in range(sem * 7, (sem + 1) * 7)
                        if ((d + offset_dia) % 7) < 5 and d not in bloqueados_persona]) >= dias_min_seguimiento
            ]
            semanas_candidatas_global = len(semanas_indices)
            # Si la suma de semanas requeridas supera las disponibles, hay competencia entre tipos
            # En ese caso relajamos a <= para no generar infeasibility
            hay_conflicto = total_semanas_requeridas > semanas_candidatas_global
            
            if DEBUG_LOGS and (total_semanas_requeridas > 0):
                print(f"Diagnostico {nombre}: Requiere {total_semanas_requeridas} sem. seguimiento | Disponibles: {semanas_candidatas_global} sem. (Semanas {semanas_indices})")
                if hay_conflicto:
                    print(f"  [CONFLICTO] Flexibilizando regla de seguimiento para {nombre}")

            for tipo_seg, cant_semanas in seguimientos.items():
                # Solo aplicar como regla dura los tipos "Mañana" y "Tarde"
                # Los "Indistinto" de rotativos comunes se manejan como regla blanda
                if tipo_seg == "Indistinto" and not es_jefe_coord:
                    continue

                semanas_activas = []
                semanas_candidatas = 0  # semanas donde la persona tiene dias disponibles

                # Escalar la cantidad de semanas requeridas proporcionalmente al período
                cant_semanas_escalada = round(cant_semanas * num_semanas / SEMANAS_BASE)
                # Reducir la exigencia si hay menos semanas disponibles que las requeridas
                cant_semanas_efectivo = min(cant_semanas_escalada, semanas_candidatas)
                
                # Obtener mínimo de días para considerar semana de seguimiento
                dias_min_seg = int(reglas_hard.get('dias_min_seguimiento', 4))

                for sem in range(dias_del_bloque // 7):
                    dias_lv_todos = [d for d in range(sem * 7, (sem + 1) * 7) if ((d + offset_dia) % 7) < 5]
                    dias_lv = [d for d in dias_lv_todos if d not in bloqueados_persona]

                    if len(dias_lv) < dias_min_seg:
                        continue

                    semanas_candidatas += 1
                    
                    # Capturar variantes UTI/UCO para seguimiento general
                    m_vars = [turnos[(nombre, d, t)] for d in dias_lv for t in ["Mañana_UTI", "Mañana_UCO"] if (nombre, d, t) in turnos]
                    t_vars = [turnos[(nombre, d, t)] for d in dias_lv for t in ["Tarde_UTI", "Tarde_UCO"] if (nombre, d, t) in turnos]
                    
                    # Capturar variantes específicas si el seguimiento lo pide
                    especificos = [turnos[(nombre, d, tipo_seg)] for d in dias_lv if (nombre, d, tipo_seg) in turnos]

                    cumple_sem = modelo.NewBoolVar(f'seg_{tipo_seg}_{nombre}_sem{sem}')

                    if tipo_seg.startswith("Mañana"):
                        vars_to_sum = especificos if especificos else m_vars
                        if vars_to_sum:
                            modelo.Add(sum(vars_to_sum) >= dias_min_seg).OnlyEnforceIf(cumple_sem)
                            modelo.Add(sum(vars_to_sum) < dias_min_seg).OnlyEnforceIf(cumple_sem.Not())
                    elif tipo_seg.startswith("Tarde"):
                        vars_to_sum = especificos if especificos else t_vars
                        if vars_to_sum:
                            modelo.Add(sum(vars_to_sum) >= dias_min_seg).OnlyEnforceIf(cumple_sem)
                            modelo.Add(sum(vars_to_sum) < dias_min_seg).OnlyEnforceIf(cumple_sem.Not())
                    elif tipo_seg == "Indistinto":
                        cumple_m = modelo.NewBoolVar(f'seg_ind_m_{nombre}_sem{sem}')
                        cumple_t = modelo.NewBoolVar(f'seg_ind_t_{nombre}_sem{sem}')
                        if m_vars: modelo.Add(sum(m_vars) >= dias_min_seg).OnlyEnforceIf(cumple_m)
                        if t_vars: modelo.Add(sum(t_vars) >= dias_min_seg).OnlyEnforceIf(cumple_t)
                        modelo.AddBoolOr([cumple_m, cumple_t]).OnlyEnforceIf(cumple_sem)

                    semanas_activas.append(cumple_sem)

                # Escalar la cantidad de semanas requeridas proporcionalmente al período
                cant_semanas_escalada = round(cant_semanas * num_semanas / SEMANAS_BASE)
                # Reducir la exigencia si hay menos semanas disponibles que las requeridas
                cant_semanas_efectivo = min(cant_semanas_escalada, semanas_candidatas)
                if semanas_activas:
                    if hay_conflicto:
                        modelo.Add(sum(semanas_activas) <= cant_semanas_efectivo)
                    else:
                        modelo.Add(sum(semanas_activas) == cant_semanas_efectivo)

    # 3. BALANCE DE CARGA HORARIA (DIAGNÓSTICO)
    if DEBUG_LOGS:
        print("\n--- BALANCE DE CARGA HORARIA POR SEMANA ---")
        for sem in range(num_semanas):
            horas_necesarias = 0
            for d in range(sem * 7, (sem + 1) * 7):
                es_f = ((d + offset_dia) % 7) >= 5 or d in feriados
                tipo_dia = "Finde_Feriado" if es_f else "Semana"
                for t_nombre, info in demanda_turnos[tipo_dia].items():
                    vacantes = AJUSTES_VACANTES.get(sem, {}).get(t_nombre, info["Vacantes"])
                    duracion = turnos_config.get(t_nombre, 6) if turnos_config else (12 if (es_f or t_nombre.startswith("Noche")) else 6)
                    horas_necesarias += vacantes * duracion
            
            personas_activas = []
            for _, p in df_personal.iterrows():
                if sem not in {d // 7 for d in get_dias_bloqueados(p['Nombre'])}:
                    personas_activas.append(p['Nombre'])
            
            capacidad_max = len(personas_activas) * 36
            print(f"Semana {sem}: Necesarias {horas_necesarias} hs | Capacidad Max (36h) {capacidad_max} hs | Margen: {capacidad_max - horas_necesarias} hs")
            if capacidad_max - horas_necesarias < 50:
                print(f"  [ALERTA] Margen muy bajo en Semana {sem}. Las restricciones de descanso podrian hacerla inviable.")

    # 4. COBERTURA DINÁMICA CON VALIDACIÓN
    if DEBUG_LOGS: print("\n--- VALIDACIÓN DE COBERTURA ---")
    for dia in range(dias_del_bloque):
        es_f = ((dia + offset_dia) % 7) >= 5 or dia in feriados
        tipo_dia = "Finde_Feriado" if es_f else "Semana"
        fecha_str = (fecha_inicio_dt + timedelta(days=dia)).strftime("%d/%m")
        
        for t_nombre, info in demanda_turnos[tipo_dia].items():
            sem = dia // 7
            vacantes = AJUSTES_VACANTES.get(sem, {}).get(t_nombre, info["Vacantes"])
            
            # Personas que NO están de licencia y que PUEDEN hacer este turno
            pool_posible = []
            for _, p in df_personal.iterrows():
                nombre = p['Nombre']
                bloqueados = get_dias_bloqueados(nombre)
                
                # Reglas básicas de filtrado: licencia o prohibición explícita
                if dia in bloqueados: continue
                if t_nombre == "Noche" and not p.get('Puede_Noche', True): continue
                if t_nombre in p.get('Turnos_Prohibidos_LV', []) and not es_f: continue
                
                if (nombre, dia, t_nombre) in turnos:
                    pool_posible.append(nombre)

            if vacantes > 0:
                if len(pool_posible) < vacantes:
                    print(f"[ERROR CRITICO] Dia {fecha_str} ({tipo_dia}) Turno {t_nombre}: Se necesitan {vacantes} personas pero solo hay {len(pool_posible)} disponibles: {pool_posible}")
                
                pool_vars = [turnos[(n, dia, t_nombre)] for n in pool_posible]
                modelo.Add(sum(pool_vars) == vacantes)

    # 5. LÍMITE DE 36 HORAS SEMANALES
    for index, persona in df_personal.iterrows():
        nombre = persona['Nombre']
        for sem in range(dias_del_bloque // 7):
            horas_semanales = []
            for d in range(sem * 7, (sem + 1) * 7):
                es_finde = ((d + offset_dia) % 7) >= 5 or d in feriados
                for t in (TURNOS_FINDE if es_finde else TURNOS_SEMANA):
                    if (nombre, d, t) in turnos:
                        h = turnos_config.get(t, 6) if turnos_config else (12 if (es_finde or t.startswith("Noche")) else 6)
                        horas_semanales.append(turnos[(nombre, d, t)] * h)
            if horas_semanales:
                max_h_sem = int(reglas_hard.get('max_horas_semanales', 36))
                modelo.Add(sum(horas_semanales) <= max_h_sem)

    # 6. DESCANSO POST-NOCHE (Dinámico)
    noches_nombres = [t_name for t_name, d_hs in (turnos_config or {}).items() if "Noche" in t_name] # Aproximación por nombre o es_nocturno
    # Si no hay turnos con "Noche" en el nombre, usamos el default
    if not noches_nombres: noches_nombres = ["Noche"]

    for index, persona in df_personal.iterrows():
        nombre = persona['Nombre']
        for d in range(dias_del_bloque - 1):
            for t_noche in noches_nombres:
                if (nombre, d, t_noche) in turnos:
                    siguiente_dia = [turnos[(nombre, d+1, t)] for t in (TURNOS_SEMANA + TURNOS_FINDE) if (nombre, d+1, t) in turnos]
                    for t_sig in siguiente_dia:
                        modelo.AddImplication(turnos[(nombre, d, t_noche)], t_sig.Not())

    # 7. REGLA INCOMPATIBILIDAD DÍA/NOCHE (Dinámica)
    for index, persona in df_personal.iterrows():
        nombre = persona['Nombre']
        for d in range(dias_del_bloque):
            for t_noche in noches_nombres:
                if (nombre, d, t_noche) in turnos:
                    turnos_dia = [turnos[(nombre, d, t)] for t in TURNOS_SEMANA + TURNOS_FINDE if t != t_noche and (nombre, d, t) in turnos]
                    for t_dia in turnos_dia:
                        modelo.Add(turnos[(nombre, d, t_noche)] + t_dia <= 1)

    # 8. REGLA EXCLUSIÓN MUTUA (Unicidad en el mismo bloque horario)
    for index, persona in df_personal.iterrows():
        nombre = persona['Nombre']
        for d in range(dias_del_bloque):
            # Bloque Mañana
            mañana_vars = [turnos[(nombre, d, t)] for t in ["Mañana_UTI", "Mañana_UCO", "Mañana_especial"] if (nombre, d, t) in turnos]
            if mañana_vars:
                modelo.Add(sum(mañana_vars) <= 1)
            
            # Bloque Tarde
            tarde_vars = [turnos[(nombre, d, t)] for t in ["Tarde_UTI", "Tarde_UCO", "Tarde_especial"] if (nombre, d, t) in turnos]
            if tarde_vars:
                modelo.Add(sum(tarde_vars) <= 1)
                
            # Bloque Día (Fines de semana / Feriados)
            dia_vars = [turnos[(nombre, d, t)] for t in ["Dia_UTI", "Dia_UCO"] if (nombre, d, t) in turnos]
            if dia_vars:
                modelo.Add(sum(dia_vars) <= 1)

    # CANDADO ABSOLUTO A TURNOS ESPECIALES
    lista_blanca_especiales = []
    dias_map_inv = {0: "Lunes", 1: "Martes", 2: "Miercoles", 3: "Jueves", 4: "Viernes", 5: "Sabado", 6: "Domingo"}

    for index, persona in df_personal.iterrows():
        nombre = persona['Nombre']
        for asig in persona.get('Asignaciones_Fijas', []):
            if "especial" in asig['Turno']:
                for d in range(dias_del_bloque):
                    if dias_map_inv[(d + offset_dia) % 7] == asig['Dia'] and d not in feriados:
                        lista_blanca_especiales.append((nombre, d, asig['Turno']))

    for (nombre, d, t), variable in turnos.items():
        if t in ["Mañana_especial", "Tarde_especial"]:
            if (nombre, d, t) not in lista_blanca_especiales:
                modelo.Add(variable == 0)
