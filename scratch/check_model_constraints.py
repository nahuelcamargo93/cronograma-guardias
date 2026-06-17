import sys
import os
sys.path.append(os.getcwd())

import main
import database.queries as db_queries
from database.data_loader import obtener_empleados, obtener_turnos

def run():
    print("Building model to inspect model constraints...")
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
    
    var = turnos.get(('Mora, Sergio Enrique', 2, 'G_Planta'))
    print("Variable index:", var.Index() if var is not None else "None")
    
    print("=== CONSTRAINTS INVOLVING MORA DIA 2 G_PLANTA ===")
    model_proto = modelo.Proto()
    var_idx = var.Index()
    
    # Find constraints
    for i, ct in enumerate(model_proto.constraints):
        mentioned = False
        
        # Check if var_idx is in the string representation of the constraint
        # (Very safe fallback for quick inspection)
        if str(var_idx) in str(ct):
            mentioned = True
            
        if mentioned:
            print(f"Constraint {i}: {ct.name} | Enforcement: {list(ct.enforcement_literal)}")
            # print only the first 5 lines of the constraint to keep output small
            print("\n".join(str(ct).splitlines()[:15]))
            print("-" * 50)

if __name__ == '__main__':
    run()
