import sys
import os
from datetime import date, timedelta
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import queries as db_queries
from database import schema as db_schema
from database.data_loader import obtener_empleados, obtener_turnos
from main import construir_modelo, resolver_modelo
from ortools.sat.python import cp_model

# Configuración
servicio_id = 3
fecha_inicio = "2026-07-01"
fecha_fin = "2026-07-31"

db_schema.inicializar_db()
db_queries.init_licencias(servicio_id)

fecha_inicio_dt = date.fromisoformat(fecha_inicio)
fecha_fin_dt = date.fromisoformat(fecha_fin)
total_dias = (fecha_fin_dt - fecha_inicio_dt).days + 1
offset_dia = fecha_inicio_dt.weekday()

lunes_unicos = set()
for d in range(total_dias):
    fecha_d = fecha_inicio_dt + timedelta(days=d)
    lunes = fecha_d - timedelta(days=fecha_d.weekday())
    lunes_unicos.add(lunes)
num_semanas = len(lunes_unicos)

feriados_indices = []
feriados_db = db_queries.obtener_feriados(fecha_inicio, fecha_fin, servicio_id=servicio_id)
for f_str in feriados_db:
    f_dt = date.fromisoformat(f_str)
    delta = (f_dt - fecha_inicio_dt).days
    if 0 <= delta < total_dias:
        feriados_indices.append(delta)

config_turnos, metadata_turnos_raw, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
    servicio_id=servicio_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
)
reglas_servicio_db = db_queries.cargar_reglas_servicio(servicio_id)
ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)
ajustes_servicio = db_queries.cargar_ajustes_reglas_servicio(fecha_inicio, fecha_fin, servicio_id)
ajustes_reglas['__servicio__'] = ajustes_servicio

empleados = obtener_empleados(servicio_id, fecha_inicio, total_dias)
turnos_dict = obtener_turnos(servicio_id)
historial_semana_previa = db_queries.cargar_guardias_previas(fecha_inicio, dias_atras=28, servicio_id=servicio_id)

print("Construyendo modelo con patrón forzado en MODO_DEBUG (relajación)...")
modelo, turnos, flr_tracker, ctx = construir_modelo(
    empleados, config_turnos, turnos_dict, demanda_req, ajustes_db,
    total_dias, feriados_indices, offset_dia, num_semanas,
    reglas_servicio=reglas_servicio_db,
    ajustes_reglas_personal=ajustes_reglas,
    historial_semana_previa=historial_semana_previa,
    servicio_id=servicio_id,
    fecha_inicio=fecha_inicio,
    fecha_fin=fecha_fin,
    modo_debug=True # Activar modo debug
)

from restricciones.hard._utils import is_finde as is_f

# Forzar el patrón de guardias sugerido para Sánchez Reinoso
# 6 de julio (d=5), 9 de julio (d=8), 10 de julio (d=9), 25 de julio (d=24), 28 de julio (d=27), 31 de julio (d=30)
nombre_sanchez = "Sánchez Reinoso, Ana Belén"
patron = {
    5: "G_Planta",
    8: "D_Planta",
    9: "G_Planta",
    24: "G_Planta",
    27: "G_Planta",
    30: "G_Planta"
}

# Primero, setear a 1 las indicadas
for dia, turno in patron.items():
    var_key = (nombre_sanchez, dia, turno)
    if var_key in turnos:
        modelo.Add(turnos[var_key] == 1)
        print(f"Forzado {nombre_sanchez} el día {dia} en {turno} == 1")

# Para los demás turnos en esos mismos días, forzar a 0
for dia in patron.keys():
    td = "Finde_Feriado" if is_f(dia, offset_dia, feriados_indices) else "Semana"
    for t in config_turnos.get(td, {}).keys():
        if t != patron[dia]:
            var_key = (nombre_sanchez, dia, t)
            if var_key in turnos:
                modelo.Add(turnos[var_key] == 0)

# Resolver en modo debug
df_resultados, flrs_asignados, df_cat_semanas, infracciones = resolver_modelo(
    modelo, turnos, flr_tracker, empleados, total_dias, feriados_indices, 
    fecha_inicio, offset_dia, config_turnos, ctx=ctx, max_time_in_seconds=60
)

print("\n--- INFRACCIONES DETECTADAS ---")
for codigo, detalle in infracciones:
    print(f"[{codigo}] {detalle}")
