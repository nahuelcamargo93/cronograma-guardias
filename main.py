import pandas as pd
import datetime
from datetime import date, timedelta
from ortools.sat.python import cp_model
from data import PERSONAL, asignar_horas, FECHA_INICIO, FECHA_FIN, FERIADOS, SERVICIO_ID
from hard_rules import aplicar_reglas_duras
from soft_rules import aplicar_reglas_blandas
import db as database
import rule_engine as _re

def construir_modelo(df_personal, demanda_turnos, metadata_turnos, demanda_req, ajustes_demanda, dias_del_bloque, feriados, offset_dia, num_semanas, reglas_personal, ajustes_reglas_personal=None, historial_semana_previa=None, servicio_id=1):
    modelo = cp_model.CpModel()
    flr_tracker = {} # Para trackear variables booleanas de FLR y luego leerlas

    
    mapa_dias = {
        "Lunes": 0, "Martes": 1, "Miercoles": 2, "Jueves": 3,
        "Viernes": 4, "Sabado": 5, "Domingo": 6
    }
    
    turnos = {}
    
    fecha_inicio_dt_d = date.fromisoformat(FECHA_INICIO)

    def dias_en_licencia(nombre):
        """Devuelve un set de índices de día (0-based) en que la persona está de LAR o LPP."""
        bloqueados = set()
        for licencias in (database.LAR, database.LPP):
            for (lic_ini_str, lic_fin_str) in licencias.get(nombre, []):
                lic_ini = date.fromisoformat(lic_ini_str)
                lic_fin = date.fromisoformat(lic_fin_str)
                for d in range(dias_del_bloque):
                    if lic_ini <= fecha_inicio_dt_d + timedelta(days=d) <= lic_fin:
                        bloqueados.add(d)
        return bloqueados

    for index, persona in df_personal.iterrows():
        nombre = persona['Nombre']
        licencia_dias = dias_en_licencia(nombre)
        for dia in range(dias_del_bloque):
            dia_semana = (dia + offset_dia) % 7
            es_finde_o_feriado = (dia_semana >= 5) or (dia in feriados)
            tipo_dia = "Finde_Feriado" if es_finde_o_feriado else "Semana"
            lista_turnos = demanda_turnos.get(tipo_dia, {}).keys()
    
            # 1. Definir variables para este día
            for t in lista_turnos:
                turnos[(nombre, dia, t)] = modelo.NewBoolVar(f'turno_{nombre}_dia{dia}_{t}')
    
            # 2. Forzar asignaciones fijas via rule_engine (soporta SUSPENDER y SOBRESCRIBIR)
            if dia not in licencia_dias:
                fecha_dia_str = (fecha_inicio_dt_d + timedelta(days=dia)).isoformat()
                params = _re.resolver_parametros_regla(
                    'ASIGNACION_FIJA', nombre, fecha_dia_str,
                    {}, reglas_personal, ajustes_reglas_personal or {}
                )
                # params es None si está suspendida, Ellipsis si no existe, lista si aplica
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

    aplicar_reglas_duras(modelo, turnos, df_personal, demanda_turnos, metadata_turnos, demanda_req, ajustes_demanda, dias_del_bloque, feriados, offset_dia, num_semanas, historial_semana_previa=historial_semana_previa, flr_tracker=flr_tracker, servicio_id=servicio_id)
    aplicar_reglas_blandas(modelo, turnos, df_personal, demanda_turnos, dias_del_bloque, feriados, offset_dia, num_semanas, servicio_id=servicio_id, flr_tracker=flr_tracker, historial_semana_previa=historial_semana_previa)
    
    return modelo, turnos, flr_tracker

def resolver_modelo(modelo, turnos, flr_tracker, df_personal, dias_del_bloque, feriados, fecha_inicio, offset_dia, config_turnos):
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 180
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
                for index, persona in df_personal.iterrows():
                    nombre = persona['Nombre']
                    if solver.Value(turnos[(nombre, dia, t)]) == 1:
                        resultados.append({
                            "Fecha": fecha_actual.strftime("%Y-%m-%d"),
                            "Dia_Semana": dia_semana,
                            "Turno": t,
                            "Kinesiologo": nombre
                        })

        df_resultados = pd.DataFrame(resultados)
        
        # Extraer FLR asignados
        flrs_asignados = []
        for (nombre, d), var_flr in flr_tracker.items():
            if solver.Value(var_flr) == 1:
                # El FLR dura 4 dias a partir de d
                fi = (fecha_inicio_dt + pd.Timedelta(days=d)).strftime("%Y-%m-%d")
                ff = (fecha_inicio_dt + pd.Timedelta(days=d+3)).strftime("%Y-%m-%d")
                flrs_asignados.append({
                    'nombre': nombre,
                    'fecha_inicio': fi,
                    'fecha_fin': ff
                })
        
        print(f"--- DIAGNÓSTICO FLR: Se asignaron {len(flrs_asignados)} bloques de FLR ---")
        
        return df_resultados, flrs_asignados
    elif status == cp_model.UNKNOWN:
        print("TIMEOUT: El motor no pudo encontrar una solución en el tiempo límite.")
        print("Las reglas podrían ser viables, pero la combinación de licencias y demanda hace que el problema sea muy complejo (prueba aumentar el max_time_in_seconds).")
        return None
    else:
        print("INVIABLE: Imposibilidad matemática demostrada. Las reglas, licencias y demandas entran en un conflicto lógico imposible de resolver.")
        return None, None

def main():
    # --- BASE DE DATOS: inicializar y cargar licencias ---
    database.inicializar_db()
    database.init_licencias()
    print(f"Licencias cargadas desde BD: {sum(len(v) for v in database.LAR.values())} LAR, {sum(len(v) for v in database.LPP.values())} LPP")

    df_personal = pd.DataFrame(PERSONAL)

    database.sincronizar_personal(df_personal)
    df_personal = database.cargar_datos_personales_bd(df_personal)

    # Cargar acumulados históricos desde la BD (todo anterior a FECHA_INICIO)
    historial = database.cargar_historial(df_personal, FECHA_INICIO)
    for campo in ['Horas_Anuales_Previas', 'Findes_Semanas_Previos', 'Findes_Habiles_Previos',
                  'Findes_Largos_3_Previos', 'Findes_Largos_4_Previos']:
        df_personal[campo] = df_personal['Nombre'].map(lambda n: historial.get(n, {}).get(campo, 0))

    print("--- Historial cargado desde la BD ---")
    for _, p in df_personal.iterrows():
        print(f"   {p['Nombre']:<22} {p['Horas_Anuales_Previas']:>4}hs acum | "
              f"Finde: {p['Findes_Semanas_Previos']}/{p['Findes_Habiles_Previos']} | "
              f"FL3: {p['Findes_Largos_3_Previos']} FL4: {p['Findes_Largos_4_Previos']}")

    # --- VALIDACIÓN DEL RANGO DE FECHAS ---
    fecha_inicio_dt = datetime.datetime.strptime(FECHA_INICIO, "%Y-%m-%d")
    fecha_fin_dt    = datetime.datetime.strptime(FECHA_FIN,    "%Y-%m-%d")

    if fecha_fin_dt < fecha_inicio_dt:
        raise ValueError(f"Error: FECHA_FIN ({FECHA_FIN}) es anterior a FECHA_INICIO ({FECHA_INICIO}).")

    # +1 porque ambas fechas son inclusive
    total_dias = (fecha_fin_dt - fecha_inicio_dt).days + 1

    DIAS_DEL_BLOQUE = total_dias
    num_semanas     = (DIAS_DEL_BLOQUE + 6) // 7 # Semanas aproximadas (techo)

    print(f"Periodo: {FECHA_INICIO} -> {FECHA_FIN} ({num_semanas} semanas aprox / {DIAS_DEL_BLOQUE} días)")

    feriados_indices = []
    for f_str in FERIADOS:
        f_dt = datetime.datetime.strptime(f_str, "%Y-%m-%d")
        delta = (f_dt - fecha_inicio_dt).days
        if 0 <= delta < DIAS_DEL_BLOQUE:
            feriados_indices.append(delta)

    # Cargar configuración de turnos y demanda WFM desde DB
    config_turnos, metadata_turnos, demanda_req, ajustes_db = database.cargar_configuracion_turnos(
        servicio_id=SERVICIO_ID, fecha_inicio=FECHA_INICIO, fecha_fin=FECHA_FIN
    )

    print("Construyendo el modelo de optimización...")
    offset_dia = fecha_inicio_dt.weekday()
    
    # Cargar reglas personales y ajustes temporales desde la BD
    reglas_personal_db = database.cargar_reglas_personal(servicio_id=SERVICIO_ID)
    ajustes_reglas = database.cargar_ajustes_reglas_personal(FECHA_INICIO, FECHA_FIN)
    if ajustes_reglas:
        print(f"Ajustes de reglas personales cargados: {sum(len(v) for v in ajustes_reglas.values())} registros para {len(ajustes_reglas)} personas")

    # Calcular Horas_Fijas_Semanales desde las asignaciones fijas de la BD
    def calcular_horas_fijas_db(nombre):
        asigs = reglas_personal_db.get(nombre, {}).get('ASIGNACION_FIJA', [])
        return sum(a.get('Horas', 0) for a in asigs if isinstance(a, dict))
    df_personal['Horas_Fijas_Semanales'] = df_personal['Nombre'].apply(calcular_horas_fijas_db)

    # Cargar historial de guardias previas (ultimos 7 dias antes de inicio)
    historial_semana_previa = database.cargar_guardias_previas(FECHA_INICIO, dias_atras=7)

    modelo, turnos, flr_tracker = construir_modelo(
        df_personal, config_turnos, metadata_turnos, demanda_req, ajustes_db,
        DIAS_DEL_BLOQUE, feriados_indices, offset_dia, num_semanas,
        reglas_personal=reglas_personal_db,
        ajustes_reglas_personal=ajustes_reglas,
        historial_semana_previa=historial_semana_previa,
        servicio_id=SERVICIO_ID
    )

    df_resultados, flrs_asignados = resolver_modelo(modelo, turnos, flr_tracker, df_personal, DIAS_DEL_BLOQUE, feriados_indices, FECHA_INICIO, offset_dia, config_turnos)

    if df_resultados is not None:
        if SERVICIO_ID == 1:
            import reportes.kinesiologia as reporte
            reporte.generar_y_exportar(df_resultados, df_personal, DIAS_DEL_BLOQUE, feriados_indices, FECHA_INICIO, offset_dia, config_turnos, num_semanas)
        elif SERVICIO_ID == 2:
            import reportes.enfermeria as reporte
            reporte.generar_y_exportar(df_resultados, df_personal, DIAS_DEL_BLOQUE, feriados_indices, FECHA_INICIO, offset_dia, config_turnos, num_semanas, flrs_asignados=flrs_asignados)
        else:
            print(f"[WARNING] No hay un reporte de Excel configurado para el SERVICIO_ID {SERVICIO_ID}")

        # --- ACEPTAR Y GUARDAR EN BD ---
        print("\n" + "=" * 55)
        print("  ¿Aceptar y guardar este cronograma en la base de datos?")
        print("  (El Excel ya fue generado. Esto solo persiste los datos)")
        print("=" * 55)
        resp = input("  Respuesta (s/n): ").strip().lower()
        if resp == 's':
            cronograma_id = database.guardar_cronograma(
                df_resultados, df_personal,
                FECHA_INICIO, FECHA_FIN,
                feriados_indices, offset_dia, DIAS_DEL_BLOQUE
            )
            if flrs_asignados:
                database.guardar_flrs_asignados(cronograma_id, flrs_asignados)
            print("\nCronograma guardado. La proxima generacion usara estos datos como historial.")
        else:
            print("\nCronograma NO guardado en la BD.")

if __name__ == "__main__":
    main()
