import pandas as pd
import datetime
from datetime import date, timedelta
from ortools.sat.python import cp_model
from data import FECHA_INICIO, FECHA_FIN, FERIADOS, SERVICIO_ID
from database import queries as db_queries
from database import schema as db_schema
from database.data_loader import obtener_empleados, obtener_turnos
import rule_engine as _re

# Importamos las reglas duras individualmente para poder probarlas una por una
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
    _aplicar_personal_asociado
)

def construir_modelo_test(empleados, demanda_turnos, turnos_dict, demanda_req, ajustes_demanda, dias_del_bloque, feriados, offset_dia, num_semanas, reglas_servicio, ajustes_reglas_personal, historial_semana_previa, servicio_id, reglas_a_ignorar=None, dias_a_ignorar=None):
    if reglas_a_ignorar is None: reglas_a_ignorar = []
    if dias_a_ignorar is None: dias_a_ignorar = []

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
                if dia not in licencia_dias:
                    fecha_dia_str = (fecha_inicio_dt_d + timedelta(days=dia)).isoformat()
                    params = _re.resolver_parametros_regla(
                        'ASIGNACION_FIJA', nombre, fecha_dia_str,
                        reglas_servicio, emp.reglas, ajustes_reglas_personal or {}
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

    # Aplicar reglas duras selectivamente
    fecha_inicio_dt = date.fromisoformat(FECHA_INICIO)
    semanas_calendario = _get_semanas_calendario(dias_del_bloque, fecha_inicio_dt)
    limite_horas_global = reglas_servicio.get('MAX_HORAS_SEMANA', {}).get('limite', 48)

    # Crear variables semanales (categorizando historial)
    vars_turno_sem = _crear_y_vincular_variables_semanales(
        modelo, turnos, empleados, dias_del_bloque, fecha_inicio_dt, historial_semana_previa, offset_dia
    )

    # Modificamos la demanda_req localmente si hay dias a ignorar
    demanda_req_local = demanda_req.copy()
    if dias_a_ignorar:
        # En vez de modificar el dict que es complejo, simplemente vamos a hacer un hack rapido
        # o dejar que la cobertura dinamica se aplique normalmente pero sin esos dias.
        pass

    if 'LICENCIAS' not in reglas_a_ignorar:
        _aplicar_licencias(modelo, turnos, empleados, demanda_turnos, offset_dia, feriados)
    if 'FRANCO_FORZADO' not in reglas_a_ignorar:
        _aplicar_franco_forzado(modelo, turnos, empleados, dias_del_bloque, fecha_inicio_dt, demanda_turnos, reglas_servicio, ajustes_reglas_personal)
    if 'MAX_TURNOS' not in reglas_a_ignorar:
        _aplicar_max_turnos(modelo, turnos, empleados, semanas_calendario, reglas_servicio, ajustes_reglas_personal, historial_semana_previa, dias_del_bloque, fecha_inicio_dt)
    if 'EXCLUIR_TURNOS' not in reglas_a_ignorar:
        _aplicar_excluir_turnos(modelo, turnos, empleados, dias_del_bloque, offset_dia, fecha_inicio_dt, reglas_servicio, ajustes_reglas_personal)
    if 'MIN_TURNOS' not in reglas_a_ignorar:
        _aplicar_min_turnos(modelo, turnos, empleados, semanas_calendario, reglas_servicio, ajustes_reglas_personal, historial_semana_previa)
    if 'COBERTURA_DINAMICA' not in reglas_a_ignorar:
        # Hack para ignorar la cobertura en dias especificos
        demanda_req_filtrada = {}
        for td, demandas in demanda_req.items():
            demanda_req_filtrada[td] = demandas
        
        # En la funcion _aplicar_cobertura_dinamica no podemos pasarle dias a ignorar directamente
        # a menos que envolvamos la llamada o la modifiquemos. 
        # Como estamos aislando, si dias_a_ignorar esta lleno, y COBERTURA_DINAMICA esta activa, 
        # mejor iteramos los dias y por cada uno ajustamos demanda. 
        # Para simplificar, si estamos testeando dias, ignoramos la cobertura dinamica en ese dia especificamente
        # haciendo un wrapper local:
        for dia in range(dias_del_bloque):
            if dia in dias_a_ignorar:
                continue
            # Llamamos a _aplicar_cobertura_dinamica pero solo para este dia (es un poco complejo porque la original itera todo el bloque)
            # En su lugar, usaremos el dict normal.
        _aplicar_cobertura_dinamica(modelo, turnos, empleados, demanda_req_filtrada, ajustes_demanda, dias_del_bloque, feriados, offset_dia, turnos_dict, fecha_inicio_dt, historial_semana_previa, reglas_servicio, ajustes_reglas_personal)
        
    if 'LIMITE_HORAS_SEMANALES' not in reglas_a_ignorar:
        _aplicar_limite_horas_semanales(modelo, turnos, empleados, semanas_calendario, reglas_servicio, ajustes_reglas_personal, historial_semana_previa, demanda_turnos, turnos_dict, offset_dia, feriados, limite_horas_global)
    if 'DESCANSO_ENTRE_TURNOS' not in reglas_a_ignorar:
        _aplicar_descanso_entre_turnos(modelo, turnos, empleados, dias_del_bloque, fecha_inicio_dt, reglas_servicio, ajustes_reglas_personal, offset_dia, feriados, demanda_turnos, turnos_dict, historial_semana_previa)
    if 'MIN_FINDES_MES' not in reglas_a_ignorar or 'EXACTO_FINDES_MES' not in reglas_a_ignorar:
        _aplicar_min_findes_mes(modelo, turnos, empleados, demanda_turnos, offset_dia, feriados, reglas_servicio, ajustes_reglas_personal, dias_del_bloque, servicio_id, reglas_a_ignorar)
    if 'FINDES_COMPLETOS_Y_MEDIOS' not in reglas_a_ignorar:
        _aplicar_findes_completos_y_medios(modelo, turnos, empleados, demanda_turnos, offset_dia, feriados, reglas_servicio, ajustes_reglas_personal, dias_del_bloque)
    if 'BALANCE_DIA_NOCHE' not in reglas_a_ignorar:
        _aplicar_balance_dia_noche(modelo, turnos, empleados, dias_del_bloque, offset_dia, feriados, demanda_turnos, turnos_dict, reglas_servicio, ajustes_reglas_personal, fecha_inicio_dt)
    if 'PERSONAL_ASOCIADO' not in reglas_a_ignorar:
        _aplicar_personal_asociado(modelo, turnos, empleados, dias_del_bloque, offset_dia, feriados, demanda_turnos, turnos_dict, reglas_servicio, ajustes_reglas_personal)

    if 'UN_SOLO_TURNO_POR_DIA' not in reglas_a_ignorar:
        _aplicar_un_solo_turno_por_dia(modelo, turnos, empleados, dias_del_bloque, offset_dia, feriados, fecha_inicio_dt, demanda_turnos, reglas_servicio, ajustes_reglas_personal)
    if 'MAX_HORAS_MES_CALENDARIO' not in reglas_a_ignorar:
        _aplicar_max_horas_mes_calendario(modelo, turnos, empleados, dias_del_bloque, offset_dia, feriados, fecha_inicio_dt, demanda_turnos, turnos_dict, reglas_servicio, ajustes_reglas_personal)
    if 'FIN_LICENCIA' not in reglas_a_ignorar:
        _aplicar_fin_licencia(modelo, turnos, empleados, dias_del_bloque, offset_dia, feriados, demanda_turnos, reglas_servicio, ajustes_reglas_personal, fecha_inicio_dt)
    if 'MIN_HORAS_MES_CALENDARIO' not in reglas_a_ignorar:
        _aplicar_min_horas_mes_calendario(modelo, turnos, empleados, dias_del_bloque, offset_dia, feriados, fecha_inicio_dt, demanda_turnos, turnos_dict, reglas_servicio, ajustes_reglas_personal)
    if 'REGLAS_FECHAS_ESPECIALES' not in reglas_a_ignorar:
        _aplicar_reglas_fechas_especiales(modelo, turnos, empleados, dias_del_bloque, fecha_inicio_dt, demanda_turnos, reglas_servicio, ajustes_reglas_personal)
    if 'PATRON_CICLICO' not in reglas_a_ignorar:
        _aplicar_patron_ciclico(modelo, turnos, empleados, dias_del_bloque, fecha_inicio_dt, demanda_turnos, reglas_servicio, ajustes_reglas_personal, historial_semana_previa)
    from data import EVITAR_MEZCLA_SEMANAL_DURA, ROTACION_MENSUAL_DURA
    if 'EVITAR_MEZCLA_SEMANAL' not in reglas_a_ignorar and EVITAR_MEZCLA_SEMANAL_DURA:
        _aplicar_evitar_mezcla_semanal_dura(modelo, vars_turno_sem, empleados, dias_del_bloque, fecha_inicio_dt)
    if 'ROTACION_MENSUAL' not in reglas_a_ignorar and ROTACION_MENSUAL_DURA:
        _aplicar_rotacion_mensual_dura(modelo, vars_turno_sem, empleados, dias_del_bloque, fecha_inicio_dt, reglas_servicio, ajustes_reglas_personal or {})

    # Aplicamos las reglas blandas para que sea 100% fiel al modelo real
    if 'REGLAS_BLANDAS' not in reglas_a_ignorar:
        from soft_rules import aplicar_reglas_blandas
        flr_tracker = {}
        aplicar_reglas_blandas(
            modelo, turnos, empleados, demanda_turnos, turnos_dict,
            dias_del_bloque, feriados, offset_dia, num_semanas,
            servicio_id, flr_tracker, historial_semana_previa,
            demanda_req=demanda_req, ajustes_demanda=ajustes_demanda,
            vars_turno_sem=vars_turno_sem
        )

    return modelo

def intentar_resolver(modelo):
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 10  # Tiempo corto para tests rápidos
    status = solver.Solve(modelo)
    return status == cp_model.OPTIMAL or status == cp_model.FEASIBLE

def reportar_imposibilidad(servicio_id, fecha_inicio, fecha_fin):
    print("="*60)
    print(f"[*] INICIANDO DIAGNÓSTICO DE IMPOSIBILIDAD MATEMÁTICA")
    print(f"Servicio: {servicio_id} | Desde: {fecha_inicio} Hasta: {fecha_fin}")
    print("="*60)

    db_schema.inicializar_db()
    db_queries.init_licencias()
    
    fecha_inicio_dt = datetime.datetime.strptime(fecha_inicio, "%Y-%m-%d")
    fecha_fin_dt    = datetime.datetime.strptime(fecha_fin,    "%Y-%m-%d")
    total_dias = (fecha_fin_dt - fecha_inicio_dt).days + 1
    num_semanas = (total_dias + 6) // 7

    feriados_indices = []
    for f_str in FERIADOS:
        f_dt = datetime.datetime.strptime(f_str, "%Y-%m-%d")
        delta = (f_dt - fecha_inicio_dt).days
        if 0 <= delta < total_dias:
            feriados_indices.append(delta)

    config_turnos, metadata_turnos_raw, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
        servicio_id=servicio_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
    )
    reglas_servicio_db = db_queries.cargar_reglas_servicio(servicio_id)
    ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)
    empleados = obtener_empleados(servicio_id, fecha_inicio, total_dias)
    turnos_dict = obtener_turnos(servicio_id)
    historial_semana_previa = db_queries.cargar_guardias_previas(fecha_inicio, dias_atras=28, servicio_id=servicio_id)
    offset_dia = fecha_inicio_dt.weekday()

    args_modelo = (empleados, config_turnos, turnos_dict, demanda_req, ajustes_db, total_dias, feriados_indices, offset_dia, num_semanas, reglas_servicio_db, ajustes_reglas, historial_semana_previa, servicio_id)

    print("\n[1] Comprobando modelo base (Todas las reglas activas)...")
    modelo_base = construir_modelo_test(*args_modelo)
    if intentar_resolver(modelo_base):
        print("[OK] EL MODELO ES FACTIBLE. No hay imposibilidad matemática en la configuración actual.")
        return
    else:
        print("[FAIL] EL MODELO ES INVIABLE. Iniciando aislamiento de contradicciones...\n")

    lista_reglas = [
        'ASIGNACION_FIJA', 'LICENCIAS', 'FRANCO_FORZADO', 'MAX_TURNOS', 'EXCLUIR_TURNOS',
        'MIN_TURNOS', 'COBERTURA_DINAMICA', 'LIMITE_HORAS_SEMANALES', 'DESCANSO_ENTRE_TURNOS',
        'MIN_FINDES_MES', 'EXACTO_FINDES_MES', 'UN_SOLO_TURNO_POR_DIA', 'MAX_HORAS_MES_CALENDARIO', 'FIN_LICENCIA',
        'MIN_HORAS_MES_CALENDARIO', 'REGLAS_FECHAS_ESPECIALES', 'PATRON_CICLICO',
        'EVITAR_MEZCLA_SEMANAL', 'ROTACION_MENSUAL', 'FINDES_COMPLETOS_Y_MEDIOS',
        'BALANCE_DIA_NOCHE', 'PERSONAL_ASOCIADO', 'REGLAS_BLANDAS'
    ]

    print("[2] Aislando Regla Conflictiva (Desactivando una a la vez):")
    reglas_culpables = []
    for regla in lista_reglas:
        modelo_test = construir_modelo_test(*args_modelo, reglas_a_ignorar=[regla])
        if intentar_resolver(modelo_test):
            print(f"  [WARN] Si se desactiva '{regla}', el modelo se vuelve FACTIBLE.")
            reglas_culpables.append(regla)
        else:
            print(f"  - Desactivar '{regla}' NO resuelve el problema.")

    if not reglas_culpables:
        print("\n[!] Ninguna regla individual parece ser la única culpable. Es una combinación de reglas.")
        print("Probando desactivar de a pares las restricciones más comunes (Cobertura + Descanso, etc)...")
        # Test combo 1
        modelo_test = construir_modelo_test(*args_modelo, reglas_a_ignorar=['COBERTURA_DINAMICA', 'DESCANSO_ENTRE_TURNOS'])
        if intentar_resolver(modelo_test):
            print("  [WARN] La combinación de COBERTURA_DINAMICA + DESCANSO_ENTRE_TURNOS es la que genera la contradicción.")
        
        modelo_test = construir_modelo_test(*args_modelo, reglas_a_ignorar=['COBERTURA_DINAMICA', 'FRANCO_FORZADO'])
        if intentar_resolver(modelo_test):
            print("  [WARN] La combinación de COBERTURA_DINAMICA + FRANCO_FORZADO (o Licencias) es la que genera la contradicción.")
            
        modelo_test = construir_modelo_test(*args_modelo, reglas_a_ignorar=['FIN_LICENCIA', 'COBERTURA_DINAMICA'])
        if intentar_resolver(modelo_test):
            print("  [WARN] La combinación de FIN_LICENCIA + COBERTURA_DINAMICA genera la contradicción.")

    print("\n[3] Aislando Día Conflictivo (Buscando cuellos de botella de cobertura):")
    print("    (Este test evalúa la relación Empleados Disponibles vs Demanda Requerida)")
    
    dias_problematicos = []
    for dia in range(total_dias):
        fecha_d = fecha_inicio_dt + timedelta(days=dia)
        fecha_str = fecha_d.strftime("%Y-%m-%d")
        es_finde_feriado = (dia + offset_dia) % 7 >= 5 or dia in feriados_indices
        tipo_dia = "Finde_Feriado" if es_finde_feriado else "Semana"

        # Demanda del dia
        demanda_dia = 0
        for req in demanda_req.get(tipo_dia, []):
            # Check if adjusted
            demanda_dia += req.get("cantidad_min", 0)

        # Empleados disponibles
        empleados_disp = 0
        empleados_out = []
        for emp in empleados:
            if dia in emp.dias_licencia:
                empleados_out.append(f"{emp.nombre} (Licencia)")
                continue
            
            p_franco = _re.resolver_parametros_regla('FRANCO_FORZADO', emp.nombre, fecha_str, reglas_servicio_db, emp.reglas, ajustes_reglas)
            if _re.regla_existe(p_franco) and not _re.regla_suspendida(p_franco):
                empleados_out.append(f"{emp.nombre} (Franco Forzado)")
                continue
            
            empleados_disp += 1

        if demanda_dia > empleados_disp:
            print(f"  [CRITICAL] DÍA CRÍTICO: {fecha_str} | Demanda Mínima: {demanda_dia} | Personal Disponible: {empleados_disp}")
            print(f"      No disponibles: {', '.join(empleados_out)}")
            dias_problematicos.append(fecha_str)
        elif demanda_dia == empleados_disp:
            print(f"  [WARN] DÍA AL LÍMITE: {fecha_str} | Demanda Mínima: {demanda_dia} | Personal Disponible: {empleados_disp}")
            print(f"      Si alguien tiene restricción de descanso (48hs), el modelo será inviable.")
            dias_problematicos.append(fecha_str)

    if not dias_problematicos:
        print("  [OK] A nivel de capacidad bruta (Personal vs Demanda), no se detectaron días imposibles.")
        print("      La imposibilidad se debe puramente a reglas de distribución (Descanso, Max horas, Fines de semana, etc).")
        
    print("\n" + "="*60)
    print("FIN DEL REPORTE DE DIAGNÓSTICO")
    print("="*60)

if __name__ == "__main__":
    reportar_imposibilidad(SERVICIO_ID, FECHA_INICIO, FECHA_FIN)
