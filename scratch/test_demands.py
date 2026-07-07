import datetime
from database import queries as db_queries
from database.data_loader import obtener_empleados, obtener_turnos
from utils import time_to_float

servicio_id = 4
fecha_inicio = "2026-07-01"
fecha_fin = "2026-07-31"

db_queries.init_licencias(servicio_id)
fecha_inicio_dt = datetime.datetime.strptime(fecha_inicio, "%Y-%m-%d")
fecha_fin_dt    = datetime.datetime.strptime(fecha_fin,    "%Y-%m-%d")
total_dias = (fecha_fin_dt - fecha_inicio_dt).days + 1

feriados_indices = []
feriados_db = db_queries.obtener_feriados(fecha_inicio, fecha_fin, servicio_id=servicio_id)
for f_str in feriados_db:
    f_dt = datetime.datetime.strptime(f_str, "%Y-%m-%d")
    delta = (f_dt - fecha_inicio_dt).days
    if 0 <= delta < total_dias:
        feriados_indices.append(delta)

config_turnos, metadata_turnos_raw, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
    servicio_id=servicio_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
)

print("Feriados:", feriados_db)
print("Feriados indices:", feriados_indices)

# Let's check demands for July 18th (dia = 17, which is Saturday)
dia = 17
es_f = ((dia + fecha_inicio_dt.weekday()) % 7) >= 5 or dia in feriados_indices
tipo_dia = "Finde_Feriado" if es_f else "Semana"
dia_semana_actual = (dia + fecha_inicio_dt.weekday()) % 7

print(f"\n--- Dia {dia} ({tipo_dia}, weekday={dia_semana_actual}) ---")
candidates_by_window = {}
for demanda in demanda_req.get(tipo_dia, []):
    dias_sem = demanda.get("dias_semana")
    applies = False
    if dias_sem:
        dias_validos = [int(x.strip()) for x in dias_sem.split(",") if x.strip().isdigit()]
        if dia_semana_actual in dias_validos:
            applies = True
    else:
        if dia in feriados_indices:
            applies = True
        elif tipo_dia == "Semana" and dia_semana_actual in [0, 1, 2, 3, 4]:
            applies = True
        elif tipo_dia == "Finde_Feriado" and dia_semana_actual in [5, 6]:
            applies = True

    if applies:
        puesto_key = demanda.get("puesto_id")
        key = (puesto_key, demanda["hora_inicio"], demanda["hora_fin"])
        candidates_by_window.setdefault(key, []).append(demanda)

final_demandas = []
for key, candidates in candidates_by_window.items():
    especificas = [c for c in candidates if c.get("dias_semana")]
    if especificas:
        final_demandas.extend(especificas)
    else:
        final_demandas.extend(candidates)

for dem in final_demandas:
    print(dem)
