import pandas as pd
import datetime
from datetime import date, timedelta
from ortools.sat.python import cp_model
from data import asignar_horas, FECHA_INICIO, FECHA_FIN, FERIADOS, SERVICIO_ID
from hard_rules import aplicar_reglas_duras
from soft_rules import aplicar_reglas_blandas
from database import queries as db_queries
from database import schema as db_schema
from database.data_loader import obtener_empleados, obtener_turnos
import rule_engine as _re

def construir_modelo(empleados, demanda_turnos, turnos_dict, demanda_req, ajustes_demanda, dias_del_bloque, feriados, offset_dia, num_semanas, reglas_servicio, ajustes_reglas_personal=None, historial_semana_previa=None, servicio_id=1):
    modelo = cp_model.CpModel()
    flr_tracker = {} # Para trackear variables booleanas de FLR y luego leerlas

    mapa_dias = {
        "Lunes": 0, "Martes": 1, "Miercoles": 2, "Jueves": 3,
        "Viernes": 4, "Sabado": 5, "Domingo": 6
    }
    
    turnos = {}
    fecha_inicio_dt_d = date.fromisoformat(FECHA_INICIO)

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
                t_info = turnos_dict.get(t)
                puesto_nombre_turno = t_info.puesto_nombre if t_info else None
                
                if puesto_nombre_turno and rol_persona:
                    if rol_persona != puesto_nombre_turno:
                        continue # No coincide el rol con el puesto
                
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
                        if mapa_dias.get(asig.get('Dia')) == dia_semana:
                            turno_config = asig['Turno'].replace(" ", "_")
                            vars_coincidentes = [
                                turnos[(nombre, dia, t)] for t in lista_turnos
                                if (t == turno_config or t.startswith(turno_config + "_"))
                            ]
                            if vars_coincidentes:
                                modelo.Add(sum(vars_coincidentes) == 1)
            
            # 3. Un solo turno por día (Restricción fundamental)
            vars_dia = [turnos[(nombre, dia, t)] for t in lista_turnos if (nombre, dia, t) in turnos]
            if vars_dia:
                modelo.Add(sum(vars_dia) <= 1)

    aplicar_reglas_duras(modelo, turnos, empleados, demanda_turnos, turnos_dict, demanda_req, ajustes_demanda, dias_del_bloque, feriados, offset_dia, num_semanas, historial_semana_previa, reglas_servicio, ajustes_reglas_personal, servicio_id)
    vars_turno_sem = aplicar_reglas_blandas(modelo, turnos, empleados, demanda_turnos, turnos_dict, dias_del_bloque, feriados, offset_dia, num_semanas, servicio_id, flr_tracker, historial_semana_previa)
    
    return modelo, turnos, flr_tracker, vars_turno_sem

def resolver_modelo(modelo, turnos, flr_tracker, empleados, dias_del_bloque, feriados, fecha_inicio, offset_dia, config_turnos, vars_turno_sem=None):
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 300
    solver.parameters.num_search_workers = 8 # Utilizar múltiples núcleos
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
                            "Kinesiologo": nombre
                        })

        df_resultados = pd.DataFrame(resultados)
        
        cat_semanas = []
        if vars_turno_sem:
            for (nombre, fecha_lunes), vars_tipo in vars_turno_sem.items():
                for t_tipo, var in vars_tipo.items():
                    if solver.Value(var) == 1:
                        cat_semanas.append({
                            'Nombre': nombre,
                            'Fecha_Lunes': fecha_lunes,
                            'Categoria': t_tipo
                        })
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
        return df_resultados, flrs_asignados, df_cat_semanas
    elif status == cp_model.UNKNOWN:
        print("TIMEOUT: El motor no pudo encontrar una solución en el tiempo límite.")
        return None, None, None
    else:
        print("INVIABLE: Imposibilidad matemática demostrada.")
        return None, None, None

def main():
    # --- BASE DE DATOS: inicializar y cargar licencias ---
    db_schema.inicializar_db()
    db_queries.init_licencias()
    print(f"Licencias cargadas desde BD: {sum(len(v) for v in db_queries.LAR.values())} LAR, {sum(len(v) for v in db_queries.LPP.values())} LPP")

    # VALIDACIÓN DEL RANGO DE FECHAS
    fecha_inicio_dt = datetime.datetime.strptime(FECHA_INICIO, "%Y-%m-%d")
    fecha_fin_dt    = datetime.datetime.strptime(FECHA_FIN,    "%Y-%m-%d")
    if fecha_fin_dt < fecha_inicio_dt:
        raise ValueError(f"Error: FECHA_FIN ({FECHA_FIN}) es anterior a FECHA_INICIO ({FECHA_INICIO}).")
    total_dias = (fecha_fin_dt - fecha_inicio_dt).days + 1
    DIAS_DEL_BLOQUE = total_dias
    num_semanas     = (DIAS_DEL_BLOQUE + 6) // 7

    print(f"Periodo: {FECHA_INICIO} -> {FECHA_FIN} ({num_semanas} semanas aprox / {DIAS_DEL_BLOQUE} días)")

    feriados_indices = []
    for f_str in FERIADOS:
        f_dt = datetime.datetime.strptime(f_str, "%Y-%m-%d")
        delta = (f_dt - fecha_inicio_dt).days
        if 0 <= delta < DIAS_DEL_BLOQUE:
            feriados_indices.append(delta)

    # Cargar configuración y datos vía data_loader
    config_turnos, metadata_turnos_raw, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
        servicio_id=SERVICIO_ID, fecha_inicio=FECHA_INICIO, fecha_fin=FECHA_FIN
    )
    reglas_servicio_db = db_queries.cargar_reglas_servicio(SERVICIO_ID)
    ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(FECHA_INICIO, FECHA_FIN)
    
    empleados = obtener_empleados(SERVICIO_ID, FECHA_INICIO, DIAS_DEL_BLOQUE)
    turnos_dict = obtener_turnos(SERVICIO_ID)
    
    historial_semana_previa = db_queries.cargar_guardias_previas(FECHA_INICIO, dias_atras=7)

    print("Construyendo el modelo de optimización...")
    offset_dia = fecha_inicio_dt.weekday()
    
    modelo, turnos, flr_tracker, vars_turno_sem = construir_modelo(
        empleados, config_turnos, turnos_dict, demanda_req, ajustes_db,
        DIAS_DEL_BLOQUE, feriados_indices, offset_dia, num_semanas,
        reglas_servicio=reglas_servicio_db,
        ajustes_reglas_personal=ajustes_reglas,
        historial_semana_previa=historial_semana_previa,
        servicio_id=SERVICIO_ID
    )

    df_resultados, flrs_asignados, df_cat_semanas = resolver_modelo(
        modelo, turnos, flr_tracker, empleados, DIAS_DEL_BLOQUE, feriados_indices, 
        FECHA_INICIO, offset_dia, config_turnos, vars_turno_sem=vars_turno_sem
    )

    if df_resultados is not None:
        # Reconstruir df_personal para reportes legacy
        df_personal = pd.DataFrame([vars(e) for e in empleados])
        # Renombrar campos para compatibilidad con reportes legacy si es necesario
        df_personal = df_personal.rename(columns={'nombre': 'Nombre', 'rol': 'Rol'})
        
        if SERVICIO_ID == 1:
            import reportes.kinesiologia as reporte
            reporte.generar_y_exportar(df_resultados, df_personal, DIAS_DEL_BLOQUE, feriados_indices, FECHA_INICIO, offset_dia, config_turnos, num_semanas)
        elif SERVICIO_ID == 2:
            import reportes.enfermeria as reporte
            reporte.generar_y_exportar(df_resultados, df_personal, DIAS_DEL_BLOQUE, feriados_indices, FECHA_INICIO, offset_dia, config_turnos, num_semanas, flrs_asignados=flrs_asignados, df_cat_semanas=df_cat_semanas)
        elif SERVICIO_ID == 3:
            import reportes.medicos as reporte
            reporte.generar_y_exportar(df_resultados, df_personal, DIAS_DEL_BLOQUE, feriados_indices, FECHA_INICIO, offset_dia, config_turnos, num_semanas)

        print("\n" + "=" * 55)
        print("  ¿Aceptar y guardar este cronograma en la base de datos?")
        print("=" * 55)
        resp = input("  Respuesta (s/n): ").strip().lower()
        if resp == 's':
            cronograma_id = db_queries.guardar_cronograma(
                df_resultados, df_personal,
                FECHA_INICIO, FECHA_FIN,
                feriados_indices, offset_dia, DIAS_DEL_BLOQUE
            )
            if flrs_asignados:
                db_queries.guardar_flrs_asignados(cronograma_id, flrs_asignados)
            print("\nCronograma guardado.")

if __name__ == "__main__":
    main()
