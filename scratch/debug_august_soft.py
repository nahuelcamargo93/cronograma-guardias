import sys
import os
import datetime
from ortools.sat.python import cp_model

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from main import construir_modelo, resolver_modelo
from database import queries as db_queries
from database import schema as db_schema
from database.data_loader import obtener_empleados, obtener_turnos

def main():
    servicio_id = 2
    fecha_inicio = "2026-08-01"
    fecha_fin = "2026-09-06"  # Planificando toda la semana 36

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

    print(f"Construyendo modelo para Servicio {servicio_id} del {fecha_inicio} al {fecha_fin}...")
    
    # Construimos el modelo con modo_debug=True (relaja restricciones hard)
    modelo, turnos, flr_tracker, ctx = construir_modelo(
        empleados, config_turnos, turnos_dict, demanda_req, ajustes_db,
        total_dias, feriados_indices, offset_dia, num_semanas,
        reglas_servicio=reglas_servicio_db,
        ajustes_reglas_personal=ajustes_reglas,
        historial_semana_previa=historial_semana_previa,
        servicio_id=servicio_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        modo_debug=True,
        force_assumptions=False,
        asignaciones_fijas_eventuales={},
        asignaciones_fijas_recurrentes={},
        francos_forzados=set()
    )

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 100
    solver.parameters.num_search_workers = 4
    
    print("Resolviendo...")
    status = solver.Solve(modelo)
    
    print(f"Estado de resolución: {solver.StatusName(status)}")
    
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        print("\n--- INFRACCIONES DE REGLAS DETECTADAS (MODO DEBUG SOFT) ---")
        infracciones_hard = []
        for peso, var in ctx.penalizaciones:
            val = solver.Value(var)
            if val > 0:
                infracciones_hard.append((var.Name(), val))
        
        if infracciones_hard:
            print(f"Se encontraron {len(infracciones_hard)} violaciones de restricciones hard:")
            for name, val in sorted(infracciones_hard):
                print(f"  -> {name} = {val}")
        else:
            print("No se encontraron violaciones de restricciones hard.")
            
        print("\n--- RESUMEN DE VARIABLES DE TURNOS ASIGNADOS POR PERSONA Y DÍA ---")
        # Mostrar asignaciones de personas para diagnosticar
        for emp in empleados:
            dias_t = []
            for d in range(total_dias):
                for t in config_turnos.get("Semana" if (d+offset_dia)%7 < 5 and d not in feriados_indices else "Finde_Feriado", {}).keys():
                    if (emp.nombre, d, t) in turnos and solver.Value(turnos[(emp.nombre, d, t)]) == 1:
                        dias_t.append(f"d{d}:{t}")
            if dias_t:
                print(f"{emp.nombre}: {', '.join(dias_t)}")
    else:
        print("El modelo con modo_debug=True sigue siendo INFEASIBLE. Esto indica que hay un error estructural en la creación de variables o dependencias.")

if __name__ == "__main__":
    main()
