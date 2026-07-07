import sys
sys.path.insert(0, '.')
import datetime
from database import schema as db_schema
from database import queries as db_queries
from database.data_loader import obtener_empleados, obtener_turnos
from main import construir_modelo
import copy

db_schema.inicializar_db()
servicio_id = 2
fecha_inicio = "2026-08-01"

fecha_inicio_dt = datetime.datetime.strptime(fecha_inicio, "%Y-%m-%d")
total_dias = 31
DIAS_DEL_BLOQUE = total_dias

# Calcular semanas
lunes_unicos = set()
for d in range(DIAS_DEL_BLOQUE):
    fecha_d = fecha_inicio_dt + datetime.timedelta(days=d)
    lunes = fecha_d - datetime.timedelta(days=fecha_d.weekday())
    lunes_unicos.add(lunes.date())
num_semanas = len(lunes_unicos)

feriados_indices = []
feriados_db = db_queries.obtener_feriados(fecha_inicio, "2026-08-31", servicio_id=servicio_id)
for f_str in feriados_db:
    f_dt = datetime.datetime.strptime(f_str, "%Y-%m-%d")
    delta = (f_dt - fecha_inicio_dt).days
    if 0 <= delta < DIAS_DEL_BLOQUE:
        feriados_indices.append(delta)

config_turnos, metadata_turnos_raw, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
    servicio_id=servicio_id, fecha_inicio=fecha_inicio, fecha_fin="2026-08-31"
)
reglas_servicio_db = db_queries.cargar_reglas_servicio(servicio_id)
ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, "2026-08-31")
ajustes_servicio = db_queries.cargar_ajustes_reglas_servicio(fecha_inicio, "2026-08-31", servicio_id)
ajustes_reglas['__servicio__'] = ajustes_servicio

empleados = obtener_empleados(servicio_id, fecha_inicio, DIAS_DEL_BLOQUE)
turnos_dict = obtener_turnos(servicio_id)
historial_semana_previa = db_queries.cargar_guardias_previas(fecha_inicio, dias_atras=28, servicio_id=servicio_id)
offset_dia = fecha_inicio_dt.weekday()

# Construir el modelo
modelo_t, turnos_t, flr_t, ctx_t = construir_modelo(
    empleados, config_turnos, turnos_dict, demanda_req, ajustes_db,
    DIAS_DEL_BLOQUE, feriados_indices, offset_dia, num_semanas,
    reglas_servicio=reglas_servicio_db,
    ajustes_reglas_personal=ajustes_reglas,
    historial_semana_previa=historial_semana_previa,
    servicio_id=servicio_id,
    fecha_inicio=fecha_inicio,
    fecha_fin="2026-08-31",
    modo_debug=True, # MODO DEBUG SOFT para que coincida
    force_assumptions=False,
    modo_debug_hard=False
)

proto = modelo_t.Proto()
print(f"Total variables: {len(proto.variables)}")

# Imprimir las variables 10419 y 46660 si existen
for idx in [10419, 46660]:
    if idx < len(proto.variables):
        v = proto.variables[idx]
        print(f"Var {idx}: name='{v.name}', domain={v.domain}")
    else:
        print(f"Var {idx} out of range (max={len(proto.variables)})")

# También buscar constraints que involucren a la variable con dominio fijo [1]
# La variable con dominio [1] suele ser una constante.
# Vamos a ver cuántas variables tienen dominio [1, 1] o [1] en el proto.
constantes = []
for idx, v in enumerate(proto.variables):
    if list(v.domain) == [1, 1] or list(v.domain) == [1]:
        constantes.append((idx, v.name))
print(f"Variables constantes a 1 (primeras 20): {constantes[:20]}")
