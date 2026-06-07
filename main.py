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
DEFAULT_SERVICIO_ID = 2
DEFAULT_FECHA_INICIO = "2026-07-01"
DEFAULT_MAX_TIME_IN_SECONDS = 1800
# ==============================================================================

def construir_modelo(empleados, demanda_turnos, turnos_dict, demanda_req, ajustes_demanda, dias_del_bloque, feriados, offset_dia, num_semanas, reglas_servicio, ajustes_reglas_personal=None, historial_semana_previa=None, servicio_id=1, fecha_inicio=None, fecha_fin=None, modo_debug=False, force_assumptions=False):
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

    for emp in empleados:
        nombre = emp.nombre
        rol_persona = emp.rol
        licencia_dias = emp.dias_licencia
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
            if dia not in licencia_dias:
                fecha_dia_str = (fecha_inicio_dt_d + timedelta(days=dia)).isoformat()
                params = _re.resolver_parametros_regla(
                    'ASIGNACION_FIJA', nombre, fecha_dia_str,
                    reglas_servicio, emp.reglas, ajustes_reglas_personal or {}
                )
                if _re.regla_existe(params) and isinstance(params, list):
                    for asig in params:
                        # Soporta día de semana: {"Dia": "Lunes", "Turno": "Mañana_UTI"}
                        # Y fecha puntual:       {"Fecha": "2026-06-15", "Turno": "Tarde_UCO"}
                        fecha_asig = asig.get('Fecha')
                        dia_asig   = asig.get('Dia')
                        match = (fecha_asig and fecha_asig == fecha_dia_str) or \
                                (dia_asig and mapa_dias.get(dia_asig) == dia_semana and dia not in feriados)
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
        modo_debug=modo_debug
    )
    ctx.force_assumptions = force_assumptions

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
        print(f"⚠️ Error de validación en el modelo: {validacion}")
    
    print("Resolviendo el cronograma con todas las reglas y preferencias...")
    status = solver.Solve(modelo)

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

def ejecutar_optimizacion(servicio_id, fecha_inicio, fecha_fin, notas="", modo_debug=False, max_time_in_seconds=DEFAULT_MAX_TIME_IN_SECONDS, diagnose=False):
    # --- BASE DE DATOS: inicializar y cargar licencias ---
    db_schema.inicializar_db()
    db_queries.init_licencias(servicio_id)
    
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
    
    modelo, turnos, flr_tracker, ctx = construir_modelo(
        empleados, config_turnos, turnos_dict, demanda_req, ajustes_db,
        DIAS_DEL_BLOQUE, feriados_indices, offset_dia, num_semanas,
        reglas_servicio=reglas_servicio_db,
        ajustes_reglas_personal=ajustes_reglas,
        historial_semana_previa=historial_semana_previa,
        servicio_id=servicio_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        modo_debug=modo_debug
    )

    df_resultados, flrs_asignados, df_cat_semanas, infracciones = resolver_modelo(
        modelo, turnos, flr_tracker, empleados, DIAS_DEL_BLOQUE, feriados_indices, 
        fecha_inicio, offset_dia, config_turnos, ctx=ctx, max_time_in_seconds=max_time_in_seconds
    )

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
            force_assumptions=True
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
    parser.add_argument("--fin", type=str, default=None, help="Fecha fin (YYYY-MM-DD, default: fin del mes de inicio)")
    parser.add_argument("--notas", type=str, default="Generado via CLI", help="Notas del cronograma")
    parser.add_argument("--debug", action="store_true", help="Habilitar MODO_DEBUG (relajar restricciones a penalizaciones extremas)")
    parser.add_argument("--timeout", type=int, default=DEFAULT_MAX_TIME_IN_SECONDS, help="Tiempo máximo de búsqueda en segundos")
    parser.add_argument("--diagnose", action="store_true", help="Fuerza el uso de assumptions para diagnóstico de conflictos en caso de INFEASIBLE")
    
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
            
    print(f"Ejecutando modo CLI para Servicio {args.servicio} ({fecha_inicio} -> {fecha_fin}) [DEBUG={args.debug}, TIMEOUT={args.timeout}, DIAGNOSE={args.diagnose}]...")
    res = ejecutar_optimizacion(args.servicio, fecha_inicio, fecha_fin, notas=args.notas, modo_debug=args.debug, max_time_in_seconds=args.timeout, diagnose=args.diagnose)
    print(res)


if __name__ == "__main__":
    main()
