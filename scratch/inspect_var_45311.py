import sys
sys.path.insert(0, '.')
import sqlite3
from main import construir_modelo
from database.data_loader import obtener_empleados, obtener_turnos
import datetime
from datetime import date
import database.queries as db_queries

conn = sqlite3.connect('cronograma_inteligente.db')

try:
    servicio_id = 2
    fecha_inicio = "2026-08-01"
    dias_del_bloque = 31
    fecha_fin = "2026-08-31"

    config_turnos, metadata_turnos_raw, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
        servicio_id=servicio_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
    )
    reglas_servicio_db = db_queries.cargar_reglas_servicio(servicio_id)
    ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)
    
    ajustes_servicio = db_queries.cargar_ajustes_reglas_servicio(fecha_inicio, fecha_fin, servicio_id)
    ajustes_reglas['__servicio__'] = ajustes_servicio
    
    empleados = obtener_empleados(servicio_id, fecha_inicio, dias_del_bloque)
    turnos_dict = obtener_turnos(servicio_id)
    
    historial_semana_previa = db_queries.cargar_guardias_previas(fecha_inicio, dias_atras=28, servicio_id=servicio_id)

    # Cargar feriados
    fecha_inicio_dt = date.fromisoformat(fecha_inicio)
    fecha_fin_dt = date.fromisoformat(fecha_fin)
    feriados_indices = []
    feriados_db = db_queries.obtener_feriados(fecha_inicio, fecha_fin, servicio_id=servicio_id)
    for f_str in feriados_db:
        f_dt = datetime.datetime.strptime(f_str, "%Y-%m-%d")
        delta = (f_dt.date() - fecha_inicio_dt).days
        if 0 <= delta < dias_del_bloque:
            feriados_indices.append(delta)

    offset_dia = fecha_inicio_dt.weekday()
    lunes_unicos = set()
    for d in range(dias_del_bloque):
        fecha_d = fecha_inicio_dt + datetime.timedelta(days=d)
        lunes = fecha_d - datetime.timedelta(days=fecha_d.weekday())
        lunes_unicos.add(lunes)
    num_semanas = len(lunes_unicos)

    modelo, turnos, flr_tracker, ctx = construir_modelo(
        empleados, config_turnos, turnos_dict, demanda_req, ajustes_db,
        dias_del_bloque, feriados_indices, offset_dia, num_semanas,
        reglas_servicio=reglas_servicio_db,
        ajustes_reglas_personal=ajustes_reglas,
        historial_semana_previa=historial_semana_previa,
        servicio_id=servicio_id,
        fecha_inicio=fecha_inicio,
        fecha_fin="2026-08-31"
    )

    proto = modelo.Proto()
    var_names = {i: var.name for i, var in enumerate(proto.variables)}
    
    print("Variable 45311 name:", var_names.get(45311, "not found"))

finally:
    conn.close()
