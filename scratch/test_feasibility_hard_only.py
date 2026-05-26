import sqlite3
import datetime
from datetime import date, timedelta
import pandas as pd
from ortools.sat.python import cp_model
from data import FECHA_INICIO, FECHA_FIN, FERIADOS, SERVICIO_ID
from hard_rules import aplicar_reglas_duras
from database import queries as db_queries
from database import schema as db_schema
from database.data_loader import obtener_empleados, obtener_turnos

def main():
    print("Probando viabilidad con REGLAS DURAS ÚNICAMENTE...")
    db_schema.inicializar_db()
    db_queries.init_licencias()
    
    fecha_inicio_dt = datetime.datetime.strptime(FECHA_INICIO, "%Y-%m-%d")
    fecha_fin_dt    = datetime.datetime.strptime(FECHA_FIN,    "%Y-%m-%d")
    
    total_dias = (fecha_fin_dt - fecha_inicio_dt).days + 1
    DIAS_DEL_BLOQUE = total_dias
    num_semanas     = (DIAS_DEL_BLOQUE + 6) // 7

    feriados_indices = []
    for f_str in FERIADOS:
        f_dt = datetime.datetime.strptime(f_str, "%Y-%m-%d")
        delta = (f_dt - fecha_inicio_dt).days
        if 0 <= delta < DIAS_DEL_BLOQUE:
            feriados_indices.append(delta)

    # Cargar configuración y datos
    config_turnos, metadata_turnos_raw, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
        servicio_id=SERVICIO_ID, fecha_inicio=FECHA_INICIO, fecha_fin=FECHA_FIN
    )
    reglas_servicio_db = db_queries.cargar_reglas_servicio(SERVICIO_ID)
    ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(FECHA_INICIO, FECHA_FIN)
    
    empleados = obtener_empleados(SERVICIO_ID, FECHA_INICIO, DIAS_DEL_BLOQUE)
    turnos_dict = obtener_turnos(SERVICIO_ID)
    historial_semana_previa = db_queries.cargar_guardias_previas(FECHA_INICIO, dias_atras=28, servicio_id=SERVICIO_ID)
    offset_dia = fecha_inicio_dt.weekday()
    
    modelo = cp_model.CpModel()
    turnos = {}
    mapa_dias = {"Lunes": 0, "Martes": 1, "Miercoles": 2, "Jueves": 3, "Viernes": 4, "Sabado": 5, "Domingo": 6}
    
    for emp in empleados:
        nombre = emp.nombre
        rol_persona = emp.rol
        licencia_dias = emp.dias_licencia
        for dia in range(DIAS_DEL_BLOQUE):
            dia_semana = (dia + offset_dia) % 7
            es_finde_o_feriado = (dia_semana >= 5) or (dia in feriados_indices)
            tipo_dia = "Finde_Feriado" if es_finde_o_feriado else "Semana"
            lista_turnos = config_turnos.get(tipo_dia, {}).keys()
    
            for t in lista_turnos:
                t_info = turnos_dict.get(t)
                puesto_nombre_turno = t_info.puesto_nombre if t_info else None
                if puesto_nombre_turno:
                    if emp.puestos_habilitados:
                        if puesto_nombre_turno not in emp.puestos_habilitados:
                            continue
                    else:
                        if rol_persona and rol_persona != "Rotativo" and rol_persona != puesto_nombre_turno:
                            continue
                turnos[(nombre, dia, t)] = modelo.NewBoolVar(f'turno_{nombre}_dia{dia}_{t}')
    
            if dia not in licencia_dias:
                fecha_dia_str = (fecha_inicio_dt + timedelta(days=dia)).isoformat()
                params = _re_resolver_parametros_regla('ASIGNACION_FIJA', nombre, fecha_dia_str, reglas_servicio_db, emp.reglas, ajustes_reglas)
                if params and isinstance(params, list):
                    for asig in params:
                        fecha_asig = asig.get('Fecha')
                        dia_asig   = asig.get('Dia')
                        match = (fecha_asig and fecha_asig == fecha_dia_str) or (dia_asig and mapa_dias.get(dia_asig) == dia_semana)
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

    # Solo aplicamos reglas duras
    aplicar_reglas_duras(
        modelo, turnos, empleados, config_turnos, turnos_dict, demanda_req, ajustes_db,
        DIAS_DEL_BLOQUE, feriados_indices, offset_dia, num_semanas,
        historial_semana_previa, reglas_servicio_db, ajustes_reglas, SERVICIO_ID
    )
    
    # Resolver
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 60
    solver.parameters.log_search_progress = True
    
    status = solver.Solve(modelo)
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print("--- RESULTADO: FACTIBLE ---")
        print("Las reglas duras por sí solas son factibles.")
    elif status == cp_model.INFEASIBLE:
        print("--- RESULTADO: INVIABLE (INFEASIBLE) ---")
        print("Las reglas duras contienen una contradicción matemática y no se puede generar ningún cronograma.")
    else:
        print("--- RESULTADO: UNKNOWN (TIMEOUT o error) ---")

def _re_resolver_parametros_regla(codigo, persona, fecha, reglas_servicio, reglas_persona, ajustes):
    import rule_engine as _re
    return _re.resolver_parametros_regla(codigo, persona, fecha, reglas_servicio, reglas_persona, ajustes)

if __name__ == "__main__":
    main()
