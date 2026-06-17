import sys
import os
sys.path.append(os.getcwd())

import main
import database.queries as db_queries
from database.data_loader import obtener_empleados, obtener_turnos

def run():
    db_queries.init_licencias(3)
    config_turnos, _, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
        servicio_id=3, fecha_inicio="2026-07-01", fecha_fin="2026-07-31"
    )
    reglas_servicio_db = db_queries.cargar_reglas_servicio(3)
    ajustes_reglas = db_queries.cargar_ajustes_reglas_personal("2026-07-01", "2026-07-31")
    ajustes_servicio = db_queries.cargar_ajustes_reglas_servicio("2026-07-01", "2026-07-31", 3)
    ajustes_reglas['__servicio__'] = ajustes_servicio
    
    empleados = obtener_empleados(3, "2026-07-01", 31)
    turnos_dict = obtener_turnos(3)
    historial_semana_previa = db_queries.cargar_guardias_previas("2026-07-01", dias_atras=28, servicio_id=3)
    
    modelo, turnos, flr_tracker, ctx = main.construir_modelo(
        empleados, config_turnos, turnos_dict, demanda_req, ajustes_db,
        31, [19], 2, 5,
        reglas_servicio=reglas_servicio_db,
        ajustes_reglas_personal=ajustes_reglas,
        historial_semana_previa=historial_semana_previa,
        servicio_id=3,
        fecha_inicio="2026-07-01",
        fecha_fin="2026-07-31",
        modo_debug=False
    )
    
    from ortools.sat.python import cp_model
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 15
    status = solver.Solve(modelo)
    
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        print("Status is feasible/optimal!")
        print("=== GUARDIAS SOLVED FOR MORA ===")
        for d in range(31):
            for t in turnos_dict.keys():
                if ('Mora, Sergio Enrique', d, t) in turnos:
                    v = turnos[('Mora, Sergio Enrique', d, t)]
                    if solver.Value(v) == 1:
                        print(f"Day {d} (July {d+1}): {t}")
    else:
        print("Not feasible!")

if __name__ == '__main__':
    run()
