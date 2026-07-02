from numpy import False_
import pandas as pd
import datetime
from datetime import date, timedelta
from ortools.sat.python import cp_model
from restricciones.contexto import ContextoModelo
from restricciones.cargador import cargar_y_ejecutar_todas
from database import queries as db_queries
from database import schema as db_schema
from database.data_loader import obtener_empleados, obtener_turnos
import rule_engine as _re

# ==============================================================================
# CONFIGURACIÓN POR DEFECTO PARA EJECUCIÓN DIRECTA (CLI)
# Modifica estas variables para no tener que tipearlas por consola
# ==============================================================================

# Enfermeria
DEFAULT_SERVICIO_ID = 1
DEFAULT_FECHA_INICIO = "2026-08-01"
DEFAULT_FECHA_FIN = None
DEFAULT_MAX_TIME_IN_SECONDS = 60*30
DEFAULT_CRONOGRAMA_BASE_ID = None
DEFAULT_LOCK_FECHA_INICIO = None
DEFAULT_LOCK_FECHA_FIN = None
DEFAULT_DEBUG_SOFT = False
DEFAULT_DEBUG_HARD = False
DEFAULT_DIAGNOSE = False

"""

# Medicos
DEFAULT_SERVICIO_ID = 3
DEFAULT_FECHA_INICIO = "2026-07-01"
DEFAULT_FECHA_FIN = None
DEFAULT_MAX_TIME_IN_SECONDS = 200
DEFAULT_CRONOGRAMA_BASE_ID = 545
DEFAULT_LOCK_FECHA_INICIO = "2026-07-07"
DEFAULT_LOCK_FECHA_FIN = "2026-07-13"
DEFAULT_DEBUG_SOFT = False
DEFAULT_DEBUG_HARD = False
DEFAULT_DIAGNOSE = False

# ==============================================================================
"""
"""
# COM
DEFAULT_SERVICIO_ID = 4
DEFAULT_FECHA_INICIO = "2026-07-01"
DEFAULT_FECHA_FIN = None
DEFAULT_MAX_TIME_IN_SECONDS = 600
DEFAULT_CRONOGRAMA_BASE_ID = None
DEFAULT_LOCK_FECHA_INICIO = None
DEFAULT_LOCK_FECHA_FIN = None
DEFAULT_DEBUG_SOFT = False
DEFAULT_DEBUG_HARD = False
DEFAULT_DIAGNOSE = False
"""
# ======


def construir_modelo(empleados, demanda_turnos, turnos_dict, demanda_req, ajustes_demanda, dias_del_bloque, 
feriados, offset_dia, num_semanas, reglas_servicio, ajustes_reglas_personal=None, historial_semana_previa=None, 
servicio_id=1, fecha_inicio=None, fecha_fin=None, modo_debug=False, force_assumptions=False, cronograma_base_guardias=None, 
modo_debug_hard=False, exclusiones=None, lock_fecha_inicio=None, lock_fecha_fin=None, desactivar_soft=False):
    modelo = cp_model.CpModel()
    flr_tracker = {} # Para trackear variables booleanas de FLR y luego leerlas

    mapa_dias = {
        "Lunes": 0, "Martes": 1, "Miercoles": 2, "Jueves": 3,
        "Viernes": 4, "Sabado": 5, "Domingo": 6
    }
    
    turnos = {}
    if not fecha_inicio:
        raise ValueError("fecha_inicio es requerida para construir el modelo.")
    fecha_inicio_dt_d = date.fromisoformat(fecha_inicio)

    dias_bloqueados = set()
    import datetime as dt_lib
    lock_ini_dt = dt_lib.date.fromisoformat(lock_fecha_inicio) if lock_fecha_inicio else None
    lock_fin_dt = dt_lib.date.fromisoformat(lock_fecha_fin) if lock_fecha_fin else None
    if lock_ini_dt or lock_fin_dt:
        for d in range(dias_del_bloque):
            fecha_actual_d = fecha_inicio_dt_d + dt_lib.timedelta(days=d)
            es_dia_bloqueado = False
            if lock_ini_dt and lock_fin_dt:
                es_dia_bloqueado = (lock_ini_dt <= fecha_actual_d <= lock_fin_dt)
            elif lock_ini_dt:
                es_dia_bloqueado = (lock_ini_dt <= fecha_actual_d)
            elif lock_fin_dt:
                es_dia_bloqueado = (fecha_actual_d <= lock_fin_dt)
            if es_dia_bloqueado:
                dias_bloqueados.add(d)

    for emp in empleados:
        nombre = emp.nombre
        rol_persona = emp.rol
        licencia_dias = emp.dias_licencia
        if not emp.puestos_habilitados:
            print(f"[WARN] [main.py] Advertencia: El empleado '{nombre}' no tiene puestos habilitados configurados en 'personal_puestos'. Usando fallback de compatibilidad basado en su rol: '{rol_persona}'.")
        for dia in range(dias_del_bloque):
            dia_semana = (dia + offset_dia) % 7
            es_finde_o_feriado = (dia_semana >= 5) or (dia in feriados)
            tipo_dia = "Finde_Feriado" if es_finde_o_feriado else "Semana"
            lista_turnos = demanda_turnos.get(tipo_dia, {}).keys()
    
            # 1. Definir variables para este día
            for t in lista_turnos:
                # Filtrar según días permitidos (dias_semana)
                t_config = demanda_turnos.get(tipo_dia, {}).get(t, {})
                dias_hab_str = t_config.get("Dias_Habilitados", "0,1,2,3,4,5,6")
                dias_permitidos = {int(x) for x in dias_hab_str.split(",") if x.strip().isdigit()}
                
                if es_finde_o_feriado:
                    # En fines de semana y feriados, el turno debe permitir sábado (5) o domingo (6)
                    if not (5 in dias_permitidos or 6 in dias_permitidos):
                        continue
                else:
                    # En días hábiles normales, el turno debe permitir el día de la semana evaluado
                    if dia_semana not in dias_permitidos:
                        continue

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
    
            # 2. Forzar asignaciones fijas via rule_engine (soporta SUSPENDER y SOBRESCRIBIR)
            if dia not in licencia_dias and dia not in dias_bloqueados:
                fecha_dia_str = (fecha_inicio_dt_d + timedelta(days=dia)).isoformat()
                params = _re.resolver_parametros_regla(
                    'ASIGNACION_FIJA', nombre, fecha_dia_str,
                    reglas_servicio, emp.reglas, ajustes_reglas_personal or {}
                )
                if _re.regla_existe(params) and isinstance(params, list):
                    # Detectar si hay franco forzado hoy
                    params_franco = _re.resolver_parametros_regla(
                        'FRANCO_FORZADO', nombre, fecha_dia_str,
                        reglas_servicio, emp.reglas, ajustes_reglas_personal or {}
                    )
                    tiene_franco = _re.regla_existe(params_franco) and not _re.regla_suspendida(params_franco)

                    for asig in params:
                        # Soporta día de semana: {"Dia": "Lunes", "Turno": "Mañana_UTI"}
                        # Y fecha puntual:       {"Fecha": "2026-06-15", "Turno": "Tarde_UCO"}
                        fecha_asig = asig.get('Fecha')
                        dia_asig   = asig.get('Dia')
                        
                        es_por_fecha = bool(fecha_asig and fecha_asig == fecha_dia_str)
                        es_por_dia = bool(dia_asig and mapa_dias.get(dia_asig) == dia_semana and dia not in feriados)
                        
                        match = False
                        if es_por_fecha:
                            # Prevalece siempre
                            match = True
                        elif es_por_dia:
                            # Prevalece solo si no hay franco forzado
                            if not tiene_franco:
                                match = True

                        if match:
                            turno_config = asig['Turno'].replace(" ", "_")
                            vars_coincidentes = [
                                turnos[(nombre, dia, t)] for t in lista_turnos
                                if (nombre, dia, t) in turnos and (t == turno_config or t.startswith(turno_config + "_"))
                            ]
                            if vars_coincidentes:
                                modelo.Add(sum(vars_coincidentes) == 1)
            
            # 3. Un solo turno por día (Se delegó a la regla UN_TURNO_POR_DIA cargada desde el catálogo/BD)
            pass


    ctx = ContextoModelo(
        servicio_id=servicio_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        dias=dias_del_bloque,
        num_semanas=num_semanas,
        offset_dia=offset_dia,
        feriados=set(feriados),
        turnos=turnos,
        empleados=empleados,
        traductor=None,
        turnos_dict=turnos_dict,
        demanda_turnos=demanda_turnos,
        demanda_req=demanda_req,
        ajustes_demanda=ajustes_demanda,
        reglas_servicio=reglas_servicio,
        ajustes_reglas_personal=ajustes_reglas_personal,
        historial_semana_previa=historial_semana_previa,
        flr_tracker=flr_tracker,
        modo_debug=modo_debug,
        modo_debug_hard=modo_debug_hard,
        exclusiones=exclusiones or set(),
        dias_bloqueados=dias_bloqueados
    )
    ctx.force_assumptions = force_assumptions
    ctx.desactivar_soft = desactivar_soft

    # 4. Inyección de Hints (Warm Start) si hay cronograma base
    if (lock_fecha_inicio or lock_fecha_fin) and not cronograma_base_guardias:
        print("[WARN] Advertencia: Se especificó rango de bloqueo de fechas, pero no se ha provisto un cronograma base.")
        
    if cronograma_base_guardias:
        import datetime as dt_lib
        print("[Warm Start] Mapeando e inyectando hints del cronograma base...")
        fecha_inicio_dt_d = dt_lib.date.fromisoformat(fecha_inicio)
        
        # Mapear las guardias a índices de días (nombre, dia, turno)
        guardias_base_indexadas = set()
        for nombre_g, fecha_g, turno_g in cronograma_base_guardias:
            try:
                g_dt = dt_lib.date.fromisoformat(fecha_g)
                dia_idx = (g_dt - fecha_inicio_dt_d).days
                if 0 <= dia_idx < dias_del_bloque:
                    guardias_base_indexadas.add((nombre_g, dia_idx, turno_g))
            except Exception as e:
                print(f"[Warm Start] Advertencia al mapear fecha {fecha_g}: {e}")
        
        lock_ini_dt = dt_lib.date.fromisoformat(lock_fecha_inicio) if lock_fecha_inicio else None
        lock_fin_dt = dt_lib.date.fromisoformat(lock_fecha_fin) if lock_fecha_fin else None
        
        if lock_ini_dt or lock_fin_dt:
            print(f"[Bloqueo] Rango de bloqueo estricto configurado: {lock_fecha_inicio} a {lock_fecha_fin}")
            
        hints_agregados = 0
        bloqueados_agregados = 0
        for (nombre_emp, d, t), var in turnos.items():
            fecha_actual_d = fecha_inicio_dt_d + dt_lib.timedelta(days=d)
            
            es_dia_bloqueado = False
            if lock_ini_dt and lock_fin_dt:
                es_dia_bloqueado = (lock_ini_dt <= fecha_actual_d <= lock_fin_dt)
            elif lock_ini_dt:
                es_dia_bloqueado = (lock_ini_dt <= fecha_actual_d)
            elif lock_fin_dt:
                es_dia_bloqueado = (fecha_actual_d <= lock_fin_dt)
            
            es_asignado = (nombre_emp, d, t) in guardias_base_indexadas
            
            if es_dia_bloqueado:
                if es_asignado:
                    modelo.Add(var == 1)
                else:
                    modelo.Add(var == 0)
                bloqueados_agregados += 1
            else:
                if es_asignado:
                    modelo.AddHint(var, 1)
                    hints_agregados += 1
                else:
                    modelo.AddHint(var, 0)
        print(f"[Warm Start] Se inyectaron {hints_agregados} hints activos y {len(turnos) - hints_agregados - bloqueados_agregados} hints inactivos. Se bloquearon estrictamente {bloqueados_agregados} variables.")

    cargar_y_ejecutar_todas(modelo, ctx)
    
    return modelo, turnos, flr_tracker, ctx

def resolver_modelo(modelo, turnos, flr_tracker, empleados, dias_del_bloque, feriados, fecha_inicio, offset_dia, config_turnos, ctx, max_time_in_seconds=DEFAULT_MAX_TIME_IN_SECONDS):
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = max_time_in_seconds

    solver.parameters.num_search_workers = 4 # i5-6200U tiene 4 hilos lógicos
    solver.parameters.log_search_progress = True
    
    # Validar modelo antes de resolver
    validacion = modelo.Validate()
    if validacion:
        print(f"[WARN] Error de validación en el modelo: {validacion}")
    
    print("Resolviendo el cronograma con todas las reglas y preferencias...")
    status = solver.Solve(modelo)
    ctx.ultimo_status_solver = status

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print("¡CRONOGRAMA GENERADO!")
        fecha_inicio_dt = pd.to_datetime(fecha_inicio)
        resultados = []
        dias_nombres = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

        for dia in range(dias_del_bloque):
            fecha_actual = fecha_inicio_dt + pd.Timedelta(days=dia)
            dia_semana = dias_nombres[fecha_actual.weekday()]

            es_finde = ((dia + offset_dia) % 7) >= 5 or dia in feriados
            tipo_dia_res = "Finde_Feriado" if es_finde else "Semana"
            tipos_turnos = config_turnos.get(tipo_dia_res, {}).keys()

            for t in tipos_turnos:
                for emp in empleados:
                    nombre = emp.nombre
                    if (nombre, dia, t) in turnos and solver.Value(turnos[(nombre, dia, t)]) == 1:
                        resultados.append({
                            "Fecha": fecha_actual.strftime("%Y-%m-%d"),
                            "Dia_Semana": dia_semana,
                            "Turno": t,
                            "Personal": nombre
                        })

        df_resultados = pd.DataFrame(resultados)
        
        # Obtener categorías semanales del contexto/solver
        cat_semanas = []
        if ctx.vars_turno_sem:
            for (nombre, fecha_lunes), vars_tipo in ctx.vars_turno_sem.items():
                for t_tipo, var in vars_tipo.items():
                    if solver.Value(var) == 1:
                        cat_semanas.append({
                            'Nombre': nombre,
                            'Fecha_Lunes': fecha_lunes,
                            'Categoria': t_tipo
                        })
                        break # Evitar duplicados si hay más de una categoría activa (ej. en MODO_DEBUG)
        df_cat_semanas = pd.DataFrame(cat_semanas)
        
        flrs_asignados = []
        for (nombre, d), var_flr in flr_tracker.items():
            if solver.Value(var_flr) == 1:
                fi = (fecha_inicio_dt + pd.Timedelta(days=d)).strftime("%Y-%m-%d")
                ff = (fecha_inicio_dt + pd.Timedelta(days=d+3)).strftime("%Y-%m-%d")
                flrs_asignados.append({
                    'nombre': nombre,
                    'fecha_inicio': fi,
                    'fecha_fin': ff
                })
        
        print(f"--- DIAGNÓSTICO FLR: Se asignaron {len(flrs_asignados)} bloques de FLR ---")
        
        # Extraer infracciones en MODO_DEBUG
        infracciones = []
        if ctx.modo_debug:
            for peso, var in ctx.penalizaciones:
                if solver.Value(var) == 1:
                    parts = var.Name().split("__")
                    codigo_regla = parts[1] if len(parts) > 1 else "DESCONOCIDA"
                    etiqueta = "__".join(parts[2:]) if len(parts) > 2 else ""
                    infracciones.append((codigo_regla, etiqueta))
            print(f"--- DIAGNÓSTICO DEBUG: Se detectaron {len(infracciones)} infracciones de reglas ---")
            
        return df_resultados, flrs_asignados, df_cat_semanas, infracciones
    elif status == cp_model.INFEASIBLE:
        print("INVIABLE: Imposibilidad matemática demostrada.")
        if not ctx.modo_debug:
            from restricciones.cargador import reportar_conflicto
            reportar_conflicto(solver, ctx)
        return None, None, None, []
    elif status == cp_model.UNKNOWN:
        print("TIMEOUT: El motor no pudo encontrar una solución en el tiempo límite.")
        return None, None, None, []
    else:
        print(f"Estado del Solver desconocido: {status}")
        return None, None, None, []

def ejecutar_optimizacion(servicio_id, fecha_inicio, fecha_fin, notas="", modo_debug=False, max_time_in_seconds=DEFAULT_MAX_TIME_IN_SECONDS, diagnose=False, cronograma_base_id=None, modo_debug_hard=False, lock_fecha_inicio=None, lock_fecha_fin=None):
    # --- BASE DE DATOS: inicializar y cargar licencias ---
    db_schema.inicializar_db(servicio_id)
    db_queries.init_licencias(servicio_id)
    
    cronograma_base_guardias = None
    if cronograma_base_id is not None:
        print(f"Cargando cronograma base ID {cronograma_base_id} para Warm Start (hints)...")
        cronograma_base_guardias = db_queries.obtener_guardias_cronograma(cronograma_base_id)
        print(f"Se cargaron {len(cronograma_base_guardias)} guardias base.")
    
    fecha_inicio_dt = datetime.datetime.strptime(fecha_inicio, "%Y-%m-%d")
    fecha_fin_dt    = datetime.datetime.strptime(fecha_fin,    "%Y-%m-%d")
    
    if fecha_fin_dt < fecha_inicio_dt:
        return {"error": f"Error: fecha_fin ({fecha_fin}) es anterior a fecha_inicio ({fecha_inicio})."}
        
    total_dias = (fecha_fin_dt - fecha_inicio_dt).days + 1
    DIAS_DEL_BLOQUE = total_dias
    
    # Calcular semanas calendarias reales (lunes a domingo) que se solapan con el bloque
    lunes_unicos = set()
    for d in range(DIAS_DEL_BLOQUE):
        fecha_d = fecha_inicio_dt + datetime.timedelta(days=d)
        lunes = fecha_d - datetime.timedelta(days=fecha_d.weekday())
        lunes_unicos.add(lunes.date())
    num_semanas = len(lunes_unicos)

    feriados_indices = []
    feriados_db = db_queries.obtener_feriados(fecha_inicio, fecha_fin, servicio_id=servicio_id)
    for f_str in feriados_db:
        f_dt = datetime.datetime.strptime(f_str, "%Y-%m-%d")
        delta = (f_dt - fecha_inicio_dt).days
        if 0 <= delta < DIAS_DEL_BLOQUE:
            feriados_indices.append(delta)

    # Cargar configuración y datos vía data_loader
    config_turnos, metadata_turnos_raw, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
        servicio_id=servicio_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
    )
    reglas_servicio_db = db_queries.cargar_reglas_servicio(servicio_id)
    ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)
    
    # Cargar e inyectar ajustes de reglas de servicio
    ajustes_servicio = db_queries.cargar_ajustes_reglas_servicio(fecha_inicio, fecha_fin, servicio_id)
    ajustes_reglas['__servicio__'] = ajustes_servicio
    
    empleados = obtener_empleados(servicio_id, fecha_inicio, DIAS_DEL_BLOQUE)
    turnos_dict = obtener_turnos(servicio_id)
    
    historial_semana_previa = db_queries.cargar_guardias_previas(fecha_inicio, dias_atras=28, servicio_id=servicio_id)

    offset_dia = fecha_inicio_dt.weekday()
    
    # Si modo_debug_hard está activo, el modelo se construye con restricciones duras normales (modo_debug=False)
    # y assumptions forzadas para poder aislar el conflicto.
    construir_modo_debug = False if modo_debug_hard else modo_debug
    force_assumptions = True if modo_debug_hard else False

    modelo, turnos, flr_tracker, ctx = construir_modelo(
        empleados, config_turnos, turnos_dict, demanda_req, ajustes_db,
        DIAS_DEL_BLOQUE, feriados_indices, offset_dia, num_semanas,
        reglas_servicio=reglas_servicio_db,
        ajustes_reglas_personal=ajustes_reglas,
        historial_semana_previa=historial_semana_previa,
        servicio_id=servicio_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        modo_debug=construir_modo_debug,
        force_assumptions=force_assumptions,
        cronograma_base_guardias=cronograma_base_guardias,
        modo_debug_hard=modo_debug_hard,
        lock_fecha_inicio=lock_fecha_inicio,
        lock_fecha_fin=lock_fecha_fin
    )

    df_resultados, flrs_asignados, df_cat_semanas, infracciones = resolver_modelo(
        modelo, turnos, flr_tracker, empleados, DIAS_DEL_BLOQUE, feriados_indices, 
        fecha_inicio, offset_dia, config_turnos, ctx=ctx, max_time_in_seconds=max_time_in_seconds
    )

    if df_resultados is None and modo_debug_hard:
        if getattr(ctx, 'ultimo_status_solver', None) == cp_model.UNKNOWN:
            print("\n" + "="*75)
            print("  [DEBUG HARD] OMITIDO: El modelo dio TIMEOUT (UNKNOWN) en lugar de INFEASIBLE.", flush=True)
            print("  El modelo no es necesariamente inviable, sino que es complejo/lento de resolver.", flush=True)
            print("  Se recomienda subir el tiempo límite (--timeout) o usar relajación (--debug-soft).", flush=True)
            print("="*75 + "\n")
        else:
            from restricciones.debug_hard import ejecutar_diagnostico_hard
            
            codigos_reglas = list(getattr(ctx, 'reglas_duras_aplicadas', set()))
                
            def resolver_con_parametros(
                excluir_reglas=None,
                sin_licencias_de=None,
                sin_reglas_de=None,
                sin_ajustes_de=None,
                exclusiones_adicionales=None
            ):
                import copy
                
                # Clonar superficialmente la lista de empleados y clonar licencias/reglas si aplica
                empleados_clon = []
                for emp in empleados:
                    e_copy = copy.copy(emp)
                    if sin_licencias_de and emp.nombre in sin_licencias_de:
                        e_copy.dias_licencia = set()
                    else:
                        e_copy.dias_licencia = set(emp.dias_licencia)
                    
                    if sin_reglas_de and emp.nombre in sin_reglas_de:
                        e_copy.reglas = {}
                    else:
                        e_copy.reglas = dict(emp.reglas)
                    empleados_clon.append(e_copy)
                
                # Clonar ajustes de reglas de personal
                ajustes_reglas_clon = {}
                if not sin_ajustes_de:
                    ajustes_reglas_clon = copy.deepcopy(ajustes_reglas)
                else:
                    for k, v in ajustes_reglas.items():
                        if k == '__servicio__':
                            ajustes_reglas_clon[k] = v
                        elif k not in sin_ajustes_de:
                            ajustes_reglas_clon[k] = v

                # Exclusiones de reglas en ctx
                exclusiones_dict = set()
                if excluir_reglas:
                    for cod in excluir_reglas:
                        exclusiones_dict.add((cod, None))
                if exclusiones_adicionales:
                    exclusiones_dict.update(exclusiones_adicionales)
                
                modelo_t, turnos_t, flr_t, ctx_t = construir_modelo(
                    empleados_clon, config_turnos, turnos_dict, demanda_req, ajustes_db,
                    DIAS_DEL_BLOQUE, feriados_indices, offset_dia, num_semanas,
                    reglas_servicio=reglas_servicio_db,
                    ajustes_reglas_personal=ajustes_reglas_clon,
                    historial_semana_previa=historial_semana_previa,
                    servicio_id=servicio_id,
                    fecha_inicio=fecha_inicio,
                    fecha_fin=fecha_fin,
                    modo_debug=False,
                    force_assumptions=False,
                    cronograma_base_guardias=cronograma_base_guardias,
                    modo_debug_hard=False,
                    exclusiones=exclusiones_dict,
                    lock_fecha_inicio=lock_fecha_inicio,
                    lock_fecha_fin=lock_fecha_fin,
                    desactivar_soft=True
                )
                solver_t = cp_model.CpSolver()
                solver_t.parameters.max_time_in_seconds = 8
                solver_t.parameters.num_search_workers = 4
                status_t = solver_t.Solve(modelo_t)
                viable = status_t != cp_model.INFEASIBLE
                
                # Liberar explícitamente memoria de los objetos protobuf de OR-Tools
                del modelo_t
                del solver_t
                del turnos_t
                del flr_t
                del ctx_t
                import gc
                gc.collect()
                
                return viable
                
            ejecutar_diagnostico_hard(empleados, codigos_reglas, resolver_con_parametros)

    if df_resultados is None and not modo_debug and diagnose:
        print("Re-ejecutando modelo con assumptions activas para identificar conflicto...")
        modelo_ass, turnos_ass, flr_tracker_ass, ctx_ass = construir_modelo(
            empleados, config_turnos, turnos_dict, demanda_req, ajustes_db,
            DIAS_DEL_BLOQUE, feriados_indices, offset_dia, num_semanas,
            reglas_servicio=reglas_servicio_db,
            ajustes_reglas_personal=ajustes_reglas,
            historial_semana_previa=historial_semana_previa,
            servicio_id=servicio_id,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            modo_debug=modo_debug,
            force_assumptions=True,
            cronograma_base_guardias=cronograma_base_guardias,
            lock_fecha_inicio=lock_fecha_inicio,
            lock_fecha_fin=lock_fecha_fin
        )
        resolver_modelo(
            modelo_ass, turnos_ass, flr_tracker_ass, empleados, DIAS_DEL_BLOQUE, feriados_indices, 
            fecha_inicio, offset_dia, config_turnos, ctx=ctx_ass, max_time_in_seconds=30
        )

    if df_resultados is not None:
        df_personal = pd.DataFrame([vars(e) for e in empleados])
        df_personal = df_personal.rename(columns={'nombre': 'Nombre', 'rol': 'Rol'})
        
        # Guardar en BD automáticamente (para la web)
        cronograma_id = db_queries.guardar_cronograma(
            df_resultados, df_personal,
            fecha_inicio, fecha_fin,
            feriados_indices, offset_dia, DIAS_DEL_BLOQUE,
            notas=notas,
            df_cat_semanas=df_cat_semanas
        )
        if flrs_asignados:
            db_queries.guardar_flrs_asignados(cronograma_id, flrs_asignados)
            
        # Guardar infracciones si existen
        if infracciones:
            db_queries.guardar_infracciones(cronograma_id, infracciones)
            
        # --- GENERACIÓN DE REPORTE EXCEL ---
        try:
            if servicio_id == 1:
                from reportes.servicio_1_kinesiologia.kinesiologia import generar_y_exportar as gen_kin
                gen_kin(df_resultados, df_personal, DIAS_DEL_BLOQUE, feriados_indices, fecha_inicio, offset_dia, config_turnos, num_semanas, crono_id=cronograma_id)
            elif servicio_id == 2:
                from reportes.servicio_2_enfermeria.enfermeria import generar_y_exportar as gen_enf
                gen_enf(df_resultados, df_personal, DIAS_DEL_BLOQUE, feriados_indices, fecha_inicio, offset_dia, config_turnos, num_semanas, flrs_asignados, df_cat_semanas, crono_id=cronograma_id)
            elif servicio_id == 3:
                from reportes.servicio_3_medicos.medicos import generar_y_exportar as gen_med
                gen_med(df_resultados, df_personal, DIAS_DEL_BLOQUE, feriados_indices, fecha_inicio, offset_dia, config_turnos, num_semanas, flrs_asignados, df_cat_semanas, crono_id=cronograma_id)
            elif servicio_id == 4:
                from reportes.servicio_4_monitoreo.com import generar_y_exportar as gen_com
                gen_com(df_resultados, df_personal, DIAS_DEL_BLOQUE, feriados_indices, fecha_inicio, offset_dia, config_turnos, num_semanas, crono_id=cronograma_id)
            print(f"[OK] Reporte Excel generado para Servicio {servicio_id}")
        except Exception as e:
            print(f"[ERROR] Error al generar reporte Excel: {e}")
            
        return {"status": "success", "cronograma_id": cronograma_id}
    else:
        return {"status": "failed", "error": "Inviable o Timeout"}

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Motor de Optimización de Cronogramas")
    parser.add_argument("--servicio", type=int, default=DEFAULT_SERVICIO_ID, help="ID del servicio")
    parser.add_argument("--inicio", type=str, default=DEFAULT_FECHA_INICIO, help="Fecha inicio (YYYY-MM-DD)")
    parser.add_argument("--fin", type=str, default=DEFAULT_FECHA_FIN, help="Fecha fin (YYYY-MM-DD, default: fin del mes de inicio)")
    parser.add_argument("--notas", type=str, default="Generado via CLI", help="Notas del cronograma")
    
    parser.add_argument("--debug-soft", action="store_true", help="Habilitar MODO_DEBUG Soft (relajar restricciones a penalizaciones extremas)")
    parser.add_argument("--no-debug-soft", action="store_false", dest="debug_soft", help="Deshabilitar MODO_DEBUG Soft")
    parser.set_defaults(debug_soft=DEFAULT_DEBUG_SOFT)

    parser.add_argument("--debug-hard", action="store_true", help="Habilitar MODO_DEBUG Hard (diagnóstico iterativo desactivando reglas y personas)")
    parser.add_argument("--no-debug-hard", action="store_false", dest="debug_hard", help="Deshabilitar MODO_DEBUG Hard")
    parser.set_defaults(debug_hard=DEFAULT_DEBUG_HARD)

    parser.add_argument("--timeout", type=int, default=DEFAULT_MAX_TIME_IN_SECONDS, help="Tiempo máximo de búsqueda en segundos")
    
    parser.add_argument("--diagnose", action="store_true", help="Fuerza el uso de assumptions para diagnóstico de conflictos en caso de INFEASIBLE")
    parser.add_argument("--no-diagnose", action="store_false", dest="diagnose", help="Deshabilitar diagnóstico de conflictos")
    parser.set_defaults(diagnose=DEFAULT_DIAGNOSE)

    parser.add_argument("--crono-base", type=int, default=DEFAULT_CRONOGRAMA_BASE_ID, help="ID del cronograma base para Warm Start (hints)")
    parser.add_argument("--lock-inicio", type=str, default=DEFAULT_LOCK_FECHA_INICIO, help="Fecha inicio para bloquear asignaciones del cronograma base (YYYY-MM-DD)")
    parser.add_argument("--lock-fin", type=str, default=DEFAULT_LOCK_FECHA_FIN, help="Fecha fin para bloquear asignaciones del cronograma base (YYYY-MM-DD)")
    
    args = parser.parse_args()
    
    fecha_inicio = args.inicio
    fecha_fin = args.fin
    if not fecha_fin:
        import calendar
        try:
            dt = datetime.datetime.strptime(fecha_inicio, "%Y-%m-%d")
            ultimo_dia = calendar.monthrange(dt.year, dt.month)[1]
            fecha_fin = f"{dt.year}-{dt.month:02d}-{ultimo_dia:02d}"
        except Exception as e:
            print(f"Error al calcular fecha_fin automáticamente: {e}")
            fecha_fin = fecha_inicio
            
    print(f"Ejecutando modo CLI para Servicio {args.servicio} ({fecha_inicio} -> {fecha_fin}) [DEBUG_SOFT={args.debug_soft}, DEBUG_HARD={args.debug_hard}, TIMEOUT={args.timeout}, DIAGNOSE={args.diagnose}, CRONO_BASE={args.crono_base}, LOCK_INICIO={args.lock_inicio}, LOCK_FIN={args.lock_fin}]...")
    res = ejecutar_optimizacion(
        args.servicio, fecha_inicio, fecha_fin,
        notas=args.notas,
        modo_debug=args.debug_soft,
        max_time_in_seconds=args.timeout,
        diagnose=args.diagnose,
        cronograma_base_id=args.crono_base,
        modo_debug_hard=args.debug_hard,
        lock_fecha_inicio=args.lock_inicio,
        lock_fecha_fin=args.lock_fin
    )
    print(res)


if __name__ == "__main__":
    main()
