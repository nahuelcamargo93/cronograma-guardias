import sys
import os
import datetime
from ortools.sat.python import cp_model

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from main import construir_modelo
from database import queries as db_queries
from database import schema as db_schema
from database.data_loader import obtener_empleados, obtener_turnos

def main():
    servicio_id = 2
    fecha_inicio = "2026-08-01"
    fecha_fin = "2026-08-31"

    db_schema.inicializar_db()
    db_queries.init_licencias(servicio_id)
    
    fecha_inicio_dt = datetime.datetime.strptime(fecha_inicio, "%Y-%m-%d")
    fecha_fin_dt    = datetime.datetime.strptime(fecha_fin,    "%Y-%m-%d")
    total_dias = (fecha_fin_dt - fecha_inicio_dt).days + 1
    
    lunes_unicos = set()
    for d in range(total_dias):
        fecha_d = fecha_inicio_dt + datetime.timedelta(days=d)
        lunes = fecha_d - datetime.timedelta(days=fecha_d.weekday())
        lunes_unicos.add(lunes.date())
    num_semanas = len(lunes_unicos)

    feriados_indices = []
    feriados_db = db_queries.obtener_feriados(fecha_inicio, fecha_fin, servicio_id=servicio_id)
    for f_str in feriados_db:
        f_dt = datetime.datetime.strptime(f_str, "%Y-%m-%d")
        delta = (f_dt - fecha_inicio_dt).days
        if 0 <= delta < total_dias:
            feriados_indices.append(delta)

    config_turnos, turnos_info, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
        servicio_id=servicio_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
    )
    reglas_servicio_db = db_queries.cargar_reglas_servicio(servicio_id)
    ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)
    
    ajustes_servicio = db_queries.cargar_ajustes_reglas_servicio(fecha_inicio, fecha_fin, servicio_id)
    ajustes_reglas['__servicio__'] = ajustes_servicio
    
    empleados = obtener_empleados(servicio_id, fecha_inicio, total_dias)
    turnos_dict = obtener_turnos(servicio_id)
    
    historial_semana_previa = db_queries.cargar_guardias_previas(fecha_inicio, dias_atras=28, servicio_id=servicio_id)

    offset_dia = fecha_inicio_dt.weekday()

    # Bypassing construir_modelo to build a totally custom model without any rules
    modelo = cp_model.CpModel()
    
    turnos = {}
    for emp in empleados:
        nombre = emp.nombre
        for dia in range(total_dias):
            dia_semana = (dia + offset_dia) % 7
            es_finde_o_feriado = (dia_semana >= 5) or (dia in feriados_indices)
            tipo_dia = "Finde_Feriado" if es_finde_o_feriado else "Semana"
            lista_turnos = config_turnos.get(tipo_dia, {}).keys()
            for t in lista_turnos:
                turnos[(nombre, dia, t)] = modelo.NewBoolVar(f'turno_{nombre}_dia{dia}_{t}')

    # Let's solve this absolute pure model
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 5
    status = solver.Solve(modelo)
    print(f"Absolute pure model (no rules, no data loader constraints, just vars): {status == cp_model.OPTIMAL or status == cp_model.FEASIBLE}")

    # Now let's try running ONLY crear_y_vincular_variables_semanales
    from restricciones.contexto import ContextoModelo
    flr_tracker = {}
    ctx = ContextoModelo(
        servicio_id=servicio_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        dias=total_dias,
        num_semanas=num_semanas,
        offset_dia=offset_dia,
        feriados=set(feriados_indices),
        turnos=turnos,
        empleados=empleados,
        traductor=None,
        turnos_dict=turnos_dict,
        demanda_turnos=config_turnos,
        demanda_req=demanda_req,
        ajustes_demanda=ajustes_db,
        reglas_servicio=reglas_servicio_db,
        ajustes_reglas_personal=ajustes_reglas,
        historial_semana_previa=historial_semana_previa,
        flr_tracker=flr_tracker
    )

    from restricciones.hard._utils import crear_y_vincular_variables_semanales
    crear_y_vincular_variables_semanales(modelo, ctx)

    status_var = solver.Solve(modelo)
    print(f"Model with ONLY crear_y_vincular_variables_semanales: {status_var == cp_model.OPTIMAL or status_var == cp_model.FEASIBLE}")

if __name__ == "__main__":
    main()
