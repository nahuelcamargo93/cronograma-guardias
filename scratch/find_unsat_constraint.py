import sys
import os
import shutil
from ortools.sat.python import cp_model

sys.path.append(os.getcwd())

import data
import main
from database import queries as db_queries
from database.data_loader import obtener_empleados, obtener_turnos

def inspect_constraint():
    db_queries.init_licencias()
    config_turnos, metadata_turnos_raw, demanda_req, adjustments = db_queries.cargar_configuracion_turnos(
        servicio_id=data.SERVICIO_ID, fecha_inicio=data.FECHA_INICIO, fecha_fin=data.FECHA_FIN
    )
    reglas_servicio_db = db_queries.cargar_reglas_servicio(data.SERVICIO_ID)
    ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(data.FECHA_INICIO, data.FECHA_FIN)
    empleados = obtener_empleados(data.SERVICIO_ID, data.FECHA_INICIO, 31)
    turnos_dict = obtener_turnos(data.SERVICIO_ID)
    historial_semana_previa = db_queries.cargar_guardias_previas(data.FECHA_INICIO, dias_atras=28, servicio_id=data.SERVICIO_ID)
    offset_dia = 2 # July 1st 2026 is Wednesday
    
    modelo, turnos, flr_tracker, vars_turno_sem = main.construir_modelo(
        empleados, config_turnos, turnos_dict, demanda_req, adjustments,
        31, [8], offset_dia, 5, reglas_servicio_db, ajustes_reglas,
        historial_semana_previa, data.SERVICIO_ID
    )
    
    proto = modelo.Proto()
    
    # We want to print variable names for variables 1269 to 1275
    var_indices = [1269, 1270, 1271, 1272, 1273, 1274, 1275]
    print("--- VARIABLES ---")
    for idx in var_indices:
        if idx < len(proto.variables):
            v = proto.variables[idx]
            print(f"Var #{idx}: Name='{v.name}', Domain={list(v.domain)}")
        else:
            print(f"Var #{idx} out of bounds")

if __name__ == "__main__":
    inspect_constraint()
