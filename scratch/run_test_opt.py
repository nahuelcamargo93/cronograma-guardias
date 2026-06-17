import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import datetime
from ortools.sat.python import cp_model
from database import queries as db_queries
from database.data_loader import obtener_empleados, obtener_turnos
from main import construir_modelo

servicio_id = 2
fecha_inicio = "2026-07-01"
fecha_fin = "2026-07-31"

db_queries.init_licencias()

fecha_inicio_dt = datetime.datetime.strptime(fecha_inicio, "%Y-%m-%d")
fecha_fin_dt    = datetime.datetime.strptime(fecha_fin,    "%Y-%m-%d")
total_dias = (fecha_fin_dt - fecha_inicio_dt).days + 1
num_semanas     = (total_dias + 6) // 7

feriados_indices = []
feriados_db = db_queries.obtener_feriados(fecha_inicio, fecha_fin)
for f_str in feriados_db:
    f_dt = datetime.datetime.strptime(f_str, "%Y-%m-%d")
    delta = (f_dt - fecha_inicio_dt).days
    if 0 <= delta < total_dias:
        feriados_indices.append(delta)

config_turnos, turnos_dict_raw, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
    servicio_id=servicio_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
)
reglas_servicio_db = db_queries.cargar_reglas_servicio(servicio_id)
# Forzar MAX_FRANCOS_SEMANA a límite=3 y modo=SOFT
reglas_servicio_db['MAX_FRANCOS_SEMANA'] = {"limite": 3, "modo": "SOFT", "peso_soft": 10000}

ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)
ajustes_servicio = db_queries.cargar_ajustes_reglas_servicio(fecha_inicio, fecha_fin, servicio_id)
ajustes_reglas['__servicio__'] = ajustes_servicio

empleados = obtener_empleados(servicio_id, fecha_inicio, total_dias)
turnos_dict = obtener_turnos(servicio_id)
historial_semana_previa = db_queries.cargar_guardias_previas(fecha_inicio, dias_atras=28, servicio_id=servicio_id)
offset_dia = fecha_inicio_dt.weekday()

print("Construyendo modelo...")
modelo, turnos, flr_tracker, ctx = construir_modelo(
    empleados, config_turnos, turnos_dict, demanda_req, ajustes_db,
    total_dias, feriados_indices, offset_dia, num_semanas,
    reglas_servicio=reglas_servicio_db,
    ajustes_reglas_personal=ajustes_reglas,
    historial_semana_previa=historial_semana_previa,
    servicio_id=servicio_id,
    fecha_inicio=fecha_inicio,
    fecha_fin=fecha_fin,
    modo_debug=False,
    force_assumptions=False
)

from main import resolver_modelo
print("\nResolviendo modelo con MAX_FRANCOS_SEMANA en modo SOFT...")
res = resolver_modelo(
    modelo, turnos, flr_tracker, empleados, total_dias, feriados_indices,
    fecha_inicio, offset_dia, config_turnos, ctx, max_time_in_seconds=60
)

if res[0] is not None:
    df_resultados, flrs_asignados, df_cat_semanas, infracciones = res
    print("\nModelo resuelto con éxito! (FEASIBLE/OPTIMAL)")
    print(f"Total de asignaciones generadas: {len(df_resultados)}")
    print(f"Total de FLRs asignados: {len(flrs_asignados)}")
else:
    print("No se pudo resolver el modelo con MAX_FRANCOS_SEMANA en modo SOFT.")
