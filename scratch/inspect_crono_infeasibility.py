import sys
sys.path.insert(0, '.')
import datetime
from database import schema as db_schema
from database import queries as db_queries
from database.data_loader import obtener_empleados, obtener_turnos
from main import construir_modelo

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
    modo_debug=True, # MODO DEBUG SOFT
    force_assumptions=False,
    modo_debug_hard=False
)

proto = modelo_t.Proto()
print(f"Total variables: {len(proto.variables)}")
print(f"Total constraints: {len(proto.constraints)}")

# Buscar la variable de Mañe Lorena is_N_MAÑE LORENA_2026_07_27
target_var_idx = None
for idx, v in enumerate(proto.variables):
    if "is_N_MA" in v.name and "LORENA" in v.name and "2026_07_27" in v.name:
        target_var_idx = idx
        print(f"Encontrada variable objetivo: idx={idx}, name='{v.name}', domain={v.domain}")
        break

if target_var_idx is not None:
    # Buscar todas las constraints lineales donde participa esta variable
    print("\nRestricciones con esta variable:")
    for c_idx, c in enumerate(proto.constraints):
        c_str = str(c)
        # Buscar el índice en los campos del proto (vars, etc.)
        if f" {target_var_idx}\n" in c_str or f" {target_var_idx} " in c_str or f" {target_var_idx}," in c_str or f"[{target_var_idx}" in c_str or f", {target_var_idx}]" in c_str or f",{target_var_idx}" in c_str:
            print(f"Constraint {c_idx}:")
            print(c_str)

# Mostrar la constraint 50099
if 50099 < len(proto.constraints):
    print(f"\nConstraint 50099:")
    print(proto.constraints[50099])
else:
    print(f"\nConstraint 50099 is out of range (total={len(proto.constraints)})")
