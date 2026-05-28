import datetime
from datetime import date, timedelta
import json
import time
import copy
from ortools.sat.python import cp_model
from database import queries as db_queries
from database import schema as db_schema
from database.data_loader import obtener_empleados, obtener_turnos
from data import FECHA_INICIO, FECHA_FIN, FERIADOS, SERVICIO_ID
import rule_engine as _re

from hard_rules import (
    _aplicar_licencias,
    _aplicar_franco_forzado,
    _aplicar_max_turnos,
    _aplicar_excluir_turnos,
    _aplicar_min_turnos,
    _aplicar_cobertura_dinamica,
    _aplicar_limite_horas_semanales,
    _aplicar_descanso_entre_turnos,
    _aplicar_min_findes_mes,
    _aplicar_un_solo_turno_por_dia,
    _aplicar_max_horas_mes_calendario,
    _aplicar_fin_licencia,
    _aplicar_min_horas_mes_calendario,
    _aplicar_reglas_fechas_especiales,
    _aplicar_patron_ciclico,
    _get_semanas_calendario,
    _crear_y_vincular_variables_semanales,
    _aplicar_evitar_mezcla_semanal_dura,
    _aplicar_rotacion_mensual_dura,
    _aplicar_findes_completos_y_medios,
    _aplicar_balance_dia_noche,
    _aplicar_personal_asociado,
    _aplicar_max_dias_continuos,
    _is_finde
)

def construir_modelo_test_custom(empleados, demanda_turnos, turnos_dict, demanda_req, ajustes_demanda, dias_del_bloque, feriados, offset_dia, num_semanas, reglas_servicio, ajustes_reglas_personal, historial_semana_previa, servicio_id, reglas_a_ignorar=None, dias_a_ignorar=None, reglas_a_ignorar_por_persona=None):
    if reglas_a_ignorar is None: reglas_a_ignorar = []
    if dias_a_ignorar is None: dias_a_ignorar = []
    if reglas_a_ignorar_por_persona is None: reglas_a_ignorar_por_persona = {}

    ajustes_reglas_personal_copia = copy.deepcopy(ajustes_reglas_personal) if ajustes_reglas_personal else {}

    # Copiamos los empleados para no mutar los originales en memoria
    empleados_copia = []
    for emp in empleados:
        emp_copy = copy.copy(emp)
        emp_copy.dias_licencia = set(emp.dias_licencia)
        emp_copy.reglas = dict(emp.reglas)
        emp_copy.puestos_habilitados = set(emp.puestos_habilitados)
        emp_copy.puestos_primarios = set(emp.puestos_primarios)
        empleados_copia.append(emp_copy)
    empleados = empleados_copia

    # Aplicamos suspensiones por persona vía ajustes_reglas_personal_copia
    for nombre, reglas in reglas_a_ignorar_por_persona.items():
        if nombre not in ajustes_reglas_personal_copia:
            ajustes_reglas_personal_copia[nombre] = []
        for r in reglas:
            codes = [r]
            if r == 'LIMITE_HORAS_SEMANALES':
                codes = ['MAX_HORAS_SEMANA']
            elif r == 'MIN_FINDES_MES' or r == 'EXACTO_FINDES_MES':
                codes = ['MIN_FINDES_MES', 'EXACTO_FINDES_MES']
            
            for code in codes:
                ajustes_reglas_personal_copia[nombre].append({
                    'codigo_regla': code,
                    'fecha_inicio': '1970-01-01',
                    'fecha_fin': '9999-12-31',
                    'accion': 'SUSPENDER',
                    'params': None
                })
            
            if r == 'LICENCIAS':
                for emp in empleados:
                    if emp.nombre == nombre:
                        emp.dias_licencia = set()

    modelo = cp_model.CpModel()
    turnos = {}
    fecha_inicio_dt_d = date.fromisoformat(FECHA_INICIO)
    mapa_dias = {"Lunes": 0, "Martes": 1, "Miercoles": 2, "Jueves": 3, "Viernes": 4, "Sabado": 5, "Domingo": 6}

    for emp in empleados:
        nombre = emp.nombre
        rol_persona = emp.rol
        licencia_dias = emp.dias_licencia
        for dia in range(dias_del_bloque):
            dia_semana = (dia + offset_dia) % 7
            es_finde_o_feriado = (dia_semana >= 5) or (dia in feriados)
            tipo_dia = "Finde_Feriado" if es_finde_o_feriado else "Semana"
            lista_turnos = demanda_turnos.get(tipo_dia, {}).keys()
    
            for t in lista_turnos:
                t_info = turnos_dict.get(t)
                puesto_nombre_turno = t_info.puesto_nombre if t_info else None
                
                if puesto_nombre_turno:
                    if emp.puestos_habilitados:
                        if puesto_nombre_turno not in emp.puestos_habilitados:
                            continue # El empleado no está habilitado para cubrir este puesto
                    else:
                        # Fallback por compatibilidad
                        if rol_persona and rol_persona != "Rotativo" and rol_persona != puesto_nombre_turno:
                            continue
                
                turnos[(nombre, dia, t)] = modelo.NewBoolVar(f'turno_{nombre}_dia{dia}_{t}')
    
            if 'ASIGNACION_FIJA' not in reglas_a_ignorar and dia not in dias_a_ignorar:
                if not reglas_a_ignorar_por_persona or 'ASIGNACION_FIJA' not in reglas_a_ignorar_por_persona.get(nombre, []):
                    if dia not in licencia_dias:
                        fecha_dia_str = (fecha_inicio_dt_d + timedelta(days=dia)).isoformat()
                        params = _re.resolver_parametros_regla(
                            'ASIGNACION_FIJA', nombre, fecha_dia_str,
                            reglas_servicio, emp.reglas, ajustes_reglas_personal_copia or {}
                        )
                        if _re.regla_existe(params) and isinstance(params, list):
                            for asig in params:
                                fecha_asig = asig.get('Fecha')
                                dia_asig   = asig.get('Dia')
                                match = (fecha_asig and fecha_asig == fecha_dia_str) or \
                                        (dia_asig and mapa_dias.get(dia_asig) == dia_semana)
                                if match:
                                    turno_config = asig['Turno'].replace(" ", "_")
                                    vars_coincidentes = [
                                        turnos[(nombre, dia, t)] for t in lista_turnos
                                        if (nombre, dia, t) in turnos and (t == turno_config or t.startswith(turno_config + "_"))
                                    ]
                                    if vars_coincidentes:
                                        modelo.Add(sum(vars_coincidentes) == 1)
            
            vars_dia = [turnos[(nombre, dia, t)] for t in lista_turnos if (nombre, dia, t) in turnos]
            if vars_dia:
                modelo.Add(sum(vars_dia) <= 1)

    fecha_inicio_dt = date.fromisoformat(FECHA_INICIO)
    semanas_calendario = _get_semanas_calendario(dias_del_bloque, fecha_inicio_dt)
    limite_horas_global = reglas_servicio.get('MAX_HORAS_SEMANA', {}).get('limite', 48)

    # Crear variables semanales
    vars_turno_sem = _crear_y_vincular_variables_semanales(
        modelo, turnos, empleados, dias_del_bloque, fecha_inicio_dt, historial_semana_previa, offset_dia
    )

    def obtener_empleados_para_regla(nombre_regla):
        return [e for e in empleados if nombre_regla not in reglas_a_ignorar_por_persona.get(e.nombre, [])]

    if 'LICENCIAS' not in reglas_a_ignorar:
        _aplicar_licencias(modelo, turnos, empleados, demanda_turnos, offset_dia, feriados)
    if 'FRANCO_FORZADO' not in reglas_a_ignorar:
        _aplicar_franco_forzado(modelo, turnos, empleados, dias_del_bloque, fecha_inicio_dt, demanda_turnos, reglas_servicio, ajustes_reglas_personal_copia)
    if 'MAX_TURNOS' not in reglas_a_ignorar:
        _aplicar_max_turnos(modelo, turnos, empleados, semanas_calendario, reglas_servicio, ajustes_reglas_personal_copia, historial_semana_previa, dias_del_bloque, fecha_inicio_dt)
    if 'EXCLUIR_TURNOS' not in reglas_a_ignorar:
        _aplicar_excluir_turnos(modelo, turnos, empleados, dias_del_bloque, offset_dia, fecha_inicio_dt, reglas_servicio, ajustes_reglas_personal_copia)
    if 'MIN_TURNOS' not in reglas_a_ignorar:
        _aplicar_min_turnos(modelo, turnos, empleados, semanas_calendario, reglas_servicio, ajustes_reglas_personal_copia, historial_semana_previa)
    if 'COBERTURA_DINAMICA' not in reglas_a_ignorar:
        _aplicar_cobertura_dinamica(modelo, turnos, empleados, demanda_req, ajustes_demanda, dias_del_bloque, feriados, offset_dia, turnos_dict, fecha_inicio_dt, historial_semana_previa, reglas_servicio, ajustes_reglas_personal_copia)
        
    if 'LIMITE_HORAS_SEMANALES' not in reglas_a_ignorar:
        _aplicar_limite_horas_semanales(modelo, turnos, empleados, semanas_calendario, reglas_servicio, ajustes_reglas_personal_copia, historial_semana_previa, demanda_turnos, turnos_dict, offset_dia, feriados, limite_horas_global)
    if 'DESCANSO_ENTRE_TURNOS' not in reglas_a_ignorar:
        _aplicar_descanso_entre_turnos(modelo, turnos, empleados, dias_del_bloque, fecha_inicio_dt, reglas_servicio, ajustes_reglas_personal_copia, offset_dia, feriados, demanda_turnos, turnos_dict, historial_semana_previa)
    if 'MIN_FINDES_MES' not in reglas_a_ignorar or 'EXACTO_FINDES_MES' not in reglas_a_ignorar:
        _aplicar_min_findes_mes(modelo, turnos, empleados, demanda_turnos, offset_dia, feriados, reglas_servicio, ajustes_reglas_personal_copia, dias_del_bloque, servicio_id, reglas_a_ignorar)
    
    # EXACTO_FINDE_Y_DIA es manejada externamente
    
    if 'FINDES_COMPLETOS_Y_MEDIOS' not in reglas_a_ignorar:
        _aplicar_findes_completos_y_medios(modelo, turnos, empleados, demanda_turnos, offset_dia, feriados, reglas_servicio, ajustes_reglas_personal_copia, dias_del_bloque)
    if 'BALANCE_DIA_NOCHE' not in reglas_a_ignorar:
        _aplicar_balance_dia_noche(modelo, turnos, empleados, dias_del_bloque, offset_dia, feriados, demanda_turnos, turnos_dict, reglas_servicio, ajustes_reglas_personal_copia, fecha_inicio_dt)
    if 'PERSONAL_ASOCIADO' not in reglas_a_ignorar:
        _aplicar_personal_asociado(modelo, turnos, obtener_empleados_para_regla('PERSONAL_ASOCIADO'), dias_del_bloque, offset_dia, feriados, demanda_turnos, turnos_dict, reglas_servicio, ajustes_reglas_personal_copia)
    if 'MAX_DIAS_CONTINUOS' not in reglas_a_ignorar:
        _aplicar_max_dias_continuos(modelo, turnos, empleados, dias_del_bloque, fecha_inicio_dt, offset_dia, feriados, demanda_turnos, turnos_dict, reglas_servicio, ajustes_reglas_personal_copia, historial_semana_previa)

    if 'UN_SOLO_TURNO_POR_DIA' not in reglas_a_ignorar:
        _aplicar_un_solo_turno_por_dia(modelo, turnos, obtener_empleados_para_regla('UN_SOLO_TURNO_POR_DIA'), dias_del_bloque, offset_dia, feriados, fecha_inicio_dt, demanda_turnos, reglas_servicio, ajustes_reglas_personal_copia)
    if 'MAX_HORAS_MES_CALENDARIO' not in reglas_a_ignorar:
        _aplicar_max_horas_mes_calendario(modelo, turnos, empleados, dias_del_bloque, offset_dia, feriados, fecha_inicio_dt, demanda_turnos, turnos_dict, reglas_servicio, ajustes_reglas_personal_copia)
    if 'FIN_LICENCIA' not in reglas_a_ignorar:
        _aplicar_fin_licencia(modelo, turnos, obtener_empleados_para_regla('FIN_LICENCIA'), dias_del_bloque, offset_dia, feriados, demanda_turnos, reglas_servicio, ajustes_reglas_personal_copia, fecha_inicio_dt)
    if 'MIN_HORAS_MES_CALENDARIO' not in reglas_a_ignorar:
        _aplicar_min_horas_mes_calendario(modelo, turnos, empleados, dias_del_bloque, offset_dia, feriados, fecha_inicio_dt, demanda_turnos, turnos_dict, reglas_servicio, ajustes_reglas_personal_copia)
    if 'REGLAS_FECHAS_ESPECIALES' not in reglas_a_ignorar:
        _aplicar_reglas_fechas_especiales(modelo, turnos, empleados, dias_del_bloque, fecha_inicio_dt, demanda_turnos, reglas_servicio, ajustes_reglas_personal_copia)
    if 'PATRON_CICLICO' not in reglas_a_ignorar:
        _aplicar_patron_ciclico(modelo, turnos, empleados, dias_del_bloque, fecha_inicio_dt, demanda_turnos, reglas_servicio, ajustes_reglas_personal_copia, historial_semana_previa)
    from data import EVITAR_MEZCLA_SEMANAL_DURA, ROTACION_MENSUAL_DURA
    if 'EVITAR_MEZCLA_SEMANAL' not in reglas_a_ignorar and EVITAR_MEZCLA_SEMANAL_DURA:
        _aplicar_evitar_mezcla_semanal_dura(modelo, vars_turno_sem, obtener_empleados_para_regla('EVITAR_MEZCLA_SEMANAL'), dias_del_bloque, fecha_inicio_dt)
    if 'ROTACION_MENSUAL' not in reglas_a_ignorar and ROTACION_MENSUAL_DURA:
        _aplicar_rotacion_mensual_dura(modelo, vars_turno_sem, obtener_empleados_para_regla('ROTACION_MENSUAL'), dias_del_bloque, fecha_inicio_dt, reglas_servicio, ajustes_reglas_personal_copia or {})

    # Retornamos turnos para poder usarlas
    return modelo, turnos

def aplicar_exacto_finde_y_dia_condicional(modelo, turnos_vars, empleados, demanda_turnos, offset_dia, feriados, reglas_servicio, ajustes_reglas, dias_del_bloque, turnos_dict, indicator_vars):
    fecha_inicio_dt = date.fromisoformat(FECHA_INICIO)
    mapa_dias = {"lunes": 0, "martes": 1, "miercoles": 2, "jueves": 3, "viernes": 4, "sabado": 5, "domingo": 6}

    for emp in empleados:
        if emp.nombre not in indicator_vars:
            continue
            
        params = _re.resolver_parametros_regla(
            'EXACTO_FINDE_Y_DIA', emp.nombre, FECHA_INICIO,
            reglas_servicio, emp.reglas, ajustes_reglas
        )
        if not _re.regla_existe(params) or _re.regla_suspendida(params):
            continue

        modo = params.get('modo', 'HARD').upper()
        if modo != "HARD":
            continue

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
        mapping_findes = params.get('findes_por_disponibilidad')
        if mapping_findes and isinstance(mapping_findes, dict):
            target_findes = mapping_findes.get(str(k), mapping_findes.get(k, 0))
        else:
            if k >= 3:
                target_findes = 2
            elif k >= 1:
                target_findes = 1
            else:
                target_findes = 0

        mapping_dias = params.get('dias_por_disponibilidad')
        if mapping_dias and isinstance(mapping_dias, dict):
            target_dias = mapping_dias.get(str(k_dia), mapping_dias.get(k_dia, 0))
        else:
            if k_dia == 5:
                target_dias = 2
            elif k_dia in (4, 2):
                target_dias = 1
            else:
                target_dias = 0

        # --- 5. APLICAR LÓGICA DE FINES DE SEMANA ---
        vars_findes = []
        for lunes, dias in findes.items():
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
            modelo.Add(sum(vars_findes) == target_f_real).OnlyEnforceIf(indicator_vars[emp.nombre])

        # --- 6. APLICAR LÓGICA DE DÍA ESPECÍFICO ---
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
                modelo.Add(sum(vars_dia) == target_d_real).OnlyEnforceIf(indicator_vars[emp.nombre])

def run_analysis():
    print("=== INICIANDO ANÁLISIS DE MÍNIMAS DESACTIVACIONES (MILP/CP-SAT) ===", flush=True)
    print(f"Servicio ID: {SERVICIO_ID} | {FECHA_INICIO} a {FECHA_FIN}", flush=True)
    
    db_schema.inicializar_db()
    db_queries.init_licencias()
    
    fecha_inicio_dt = datetime.datetime.strptime(FECHA_INICIO, "%Y-%m-%d")
    fecha_fin_dt    = datetime.datetime.strptime(FECHA_FIN,    "%Y-%m-%d")
    total_dias = (fecha_fin_dt - fecha_inicio_dt).days + 1
    num_semanas = (total_dias + 6) // 7

    feriados_indices = []
    for f_str in FERIADOS:
        f_dt = datetime.datetime.strptime(f_str, "%Y-%m-%d")
        delta = (f_dt - fecha_inicio_dt).days
        if 0 <= delta < total_dias:
            feriados_indices.append(delta)

    config_turnos, metadata_turnos_raw, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
        servicio_id=SERVICIO_ID, fecha_inicio=FECHA_INICIO, fecha_fin=FECHA_FIN
    )
    reglas_servicio_db = db_queries.cargar_reglas_servicio(SERVICIO_ID)
    ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(FECHA_INICIO, FECHA_FIN)
    
    ajustes_servicio = db_queries.cargar_ajustes_reglas_servicio(FECHA_INICIO, FECHA_FIN, SERVICIO_ID)
    ajustes_reglas['__servicio__'] = ajustes_servicio
    
    empleados = obtener_empleados(SERVICIO_ID, FECHA_INICIO, total_dias)
    turnos_dict = obtener_turnos(SERVICIO_ID)
    historial_semana_previa = db_queries.cargar_guardias_previas(FECHA_INICIO, dias_atras=28, servicio_id=SERVICIO_ID)
    offset_dia = fecha_inicio_dt.weekday()

    # Construimos el modelo base (retorna modelo y variables de turnos)
    # Ignoramos EXACTO_FINDE_Y_DIA (la manejamos nosotros condicionalmente)
    # Ignoramos REGLAS_BLANDAS (para velocidad)
    print("Construyendo modelo con restricciones duras e indicadores...", flush=True)
    modelo, turnos_vars = construir_modelo_test_custom(
        empleados, config_turnos, turnos_dict, demanda_req, ajustes_db, total_dias, 
        feriados_indices, offset_dia, num_semanas, reglas_servicio_db, ajustes_reglas, 
        historial_semana_previa, SERVICIO_ID, reglas_a_ignorar=['EXACTO_FINDE_Y_DIA', 'REGLAS_BLANDAS']
    )

    # Creamos las variables indicadoras para EXACTO_FINDE_Y_DIA para cada profesional
    indicator_vars = {}
    for emp in empleados:
        params = _re.resolver_parametros_regla(
            'EXACTO_FINDE_Y_DIA', emp.nombre, FECHA_INICIO,
            reglas_servicio_db, emp.reglas, ajustes_reglas
        )
        if _re.regla_existe(params) and not _re.regla_suspendida(params):
            modo = params.get('modo', 'HARD').upper()
            if modo == "HARD":
                # Variable indicadora: 1 = Regla ACTIVA, 0 = Regla DESACTIVADA
                indicator_vars[emp.nombre] = modelo.NewBoolVar(f'active_exacto_{emp.nombre}')

    print(f"Profesionales con regla EXACTO_FINDE_Y_DIA en HARD: {len(indicator_vars)}", flush=True)
    for name in indicator_vars.keys():
        print(f"  - {name}", flush=True)

    # Aplicamos la regla condicionalmente
    aplicar_exacto_finde_y_dia_condicional(
        modelo, turnos_vars, empleados, config_turnos, offset_dia, feriados_indices,
        reglas_servicio_db, ajustes_reglas, total_dias, turnos_dict, indicator_vars
    )

    # Configurar función objetivo: maximizar cantidad de reglas activas (minimizar desactivaciones)
    modelo.Maximize(sum(indicator_vars.values()))

    print("Buscando la cantidad mínima de desactivaciones necesaria...", flush=True)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 60.0
    status = solver.Solve(modelo)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        print("\n[FAIL] El modelo no es viable bajo ninguna combinación de desactivaciones de esta regla.", flush=True)
        return

    max_active = int(solver.ObjectiveValue())
    num_total = len(indicator_vars)
    min_deactivations = num_total - max_active
    print(f"\nResultados de Optimización:", flush=True)
    print(f"  Total profesionales evaluados: {num_total}", flush=True)
    print(f"  Máximo de reglas que pueden estar activas a la vez: {max_active}", flush=True)
    print(f"  Mínimo de desactivaciones necesarias: {min_deactivations}", flush=True)

    # Ahora fijamos la cantidad de reglas activas a max_active para buscar todas las combinaciones posibles
    modelo.Proto().ClearField('objective') # Eliminar la función objetivo para hacer búsqueda de soluciones
    modelo.Add(sum(indicator_vars.values()) == max_active)

    print(f"\nBuscando todas las combinaciones posibles de exactamente {min_deactivations} desactivación(es)...", flush=True)
    
    soluciones = []
    sol_limit = 20
    
    while len(soluciones) < sol_limit:
        solver_iter = cp_model.CpSolver()
        solver_iter.parameters.max_time_in_seconds = 15.0
        status_iter = solver_iter.Solve(modelo)
        
        if status_iter not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            break
            
        # Extraer la combinación actual
        curr_solution = {name: int(solver_iter.Value(var)) for name, var in indicator_vars.items()}
        deactivated = sorted([name for name, val in curr_solution.items() if val == 0])
        
        if deactivated not in soluciones:
            soluciones.append(deactivated)
            print(f"  Opción {len(soluciones)}: Desactivar a {', '.join(deactivated)}", flush=True)
            
        # Añadir cláusula "no-good" para prohibir esta combinación específica de indicadores
        clause = []
        for name, var in indicator_vars.items():
            val = curr_solution[name]
            if val == 1:
                clause.append(var)
            else:
                clause.append(1 - var)
        modelo.Add(sum(clause) <= len(indicator_vars) - 1)

    print(f"\n=== REPORTE FINAL ===", flush=True)
    print(f"Se necesitan desactivar al menos {min_deactivations} persona(s) para que el cronograma sea viable.", flush=True)
    print(f"Combinaciones posibles encontradas ({len(soluciones)}):", flush=True)
    for idx, sol in enumerate(soluciones, 1):
        print(f"  Posibilidad {idx}: {', '.join(sol)}", flush=True)

if __name__ == '__main__':
    run_analysis()
