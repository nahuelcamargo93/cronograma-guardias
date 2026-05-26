import datetime
import pandas as pd
from ortools.sat.python import cp_model
from data import FECHA_INICIO, FECHA_FIN, SERVICIO_ID, FERIADOS
from database.data_loader import obtener_empleados, obtener_turnos
from database import queries as db_queries
from database import schema as db_schema
from main import construir_modelo, resolver_modelo

def test_feasibility():
    print("Iniciando prueba de factibilidad con regla dura de no mezclar turnos...")
    
    fecha_inicio = FECHA_INICIO
    fecha_fin = FECHA_FIN
    servicio_id = SERVICIO_ID
    
    fecha_inicio_dt = datetime.datetime.strptime(fecha_inicio, "%Y-%m-%d")
    fecha_fin_dt    = datetime.datetime.strptime(fecha_fin,    "%Y-%m-%d")
    total_dias = (fecha_fin_dt - fecha_inicio_dt).days + 1
    DIAS_DEL_BLOQUE = total_dias
    num_semanas     = (DIAS_DEL_BLOQUE + 6) // 7

    feriados_indices = []
    for f_str in FERIADOS:
        f_dt = datetime.datetime.strptime(f_str, "%Y-%m-%d")
        delta = (f_dt - fecha_inicio_dt).days
        if 0 <= delta < DIAS_DEL_BLOQUE:
            feriados_indices.append(delta)

    config_turnos, metadata_turnos_raw, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
        servicio_id=servicio_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
    )
    reglas_servicio_db = db_queries.cargar_reglas_servicio(servicio_id)
    ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)
    
    empleados = obtener_empleados(servicio_id, fecha_inicio, DIAS_DEL_BLOQUE)
    turnos_dict = obtener_turnos(servicio_id)
    
    historial_semana_previa = db_queries.cargar_guardias_previas(fecha_inicio, dias_atras=28, servicio_id=servicio_id)
    offset_dia = fecha_inicio_dt.weekday()
    
    # We will build the model using a temporary modification or manually in this script
    # To do it simply, we can call construir_modelo and then inspect/modify the model or just temporarily edit soft_rules.py.
    # Actually, we can temporarily edit soft_rules.py and run main.py or this test.
    # Let's do that!
    
if __name__ == '__main__':
    test_feasibility()
