import sqlite3
import json
import pandas as pd
import datetime
from datetime import date, timedelta
from ortools.sat.python import cp_model

from database import schema as db_schema
from database import queries as db_queries
from database.data_loader import obtener_empleados, obtener_turnos
from main import construir_modelo, resolver_modelo

servicio_id = 1
fecha_inicio = "2026-06-22"
fecha_fin = "2026-07-31"

db_schema.inicializar_db()
db_queries.init_licencias(servicio_id)

fecha_inicio_dt = datetime.datetime.strptime(fecha_inicio, "%Y-%m-%d")
fecha_fin_dt    = datetime.datetime.strptime(fecha_fin,    "%Y-%m-%d")
DIAS_DEL_BLOQUE = (fecha_fin_dt - fecha_inicio_dt).days + 1

# Calculate weeks
lunes_unicos = set()
for d in range(DIAS_DEL_BLOQUE):
    fecha_d = fecha_inicio_dt + datetime.timedelta(days=d)
    lunes = fecha_d - datetime.timedelta(days=fecha_d.weekday())
    lunes_unicos.add(lunes.date())
num_semanas = len(lunes_unicos)

# Feriados
feriados_indices = []
feriados_db = db_queries.obtener_feriados(fecha_inicio, fecha_fin, servicio_id=servicio_id)
for f_str in feriados_db:
    f_dt = datetime.datetime.strptime(f_str, "%Y-%m-%d")
    delta = (f_dt - fecha_inicio_dt).days
    if 0 <= delta < DIAS_DEL_BLOQUE:
        feriados_indices.append(delta)

# Load config
config_turnos, metadata_turnos_raw, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
    servicio_id=servicio_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
)

# Load rules from DB
reglas_servicio = db_queries.cargar_reglas_servicio(servicio_id)

print("=== ORIGINAL RULES ACTIVE IN DB ===")
for r_code, r_val in reglas_servicio.items():
    print(f"  {r_code}: {r_val.get('activo', 1) if isinstance(r_val, dict) else 1}")

# MODIFY RULES IN MEMORY FOR SIMULATION
# 1. Activate MANEJO_FINDES and correct its historical date
if 'MANEJO_FINDES' in reglas_servicio:
    reglas_servicio['MANEJO_FINDES']['activo'] = 1
    if 'nivelacion_historica' in reglas_servicio['MANEJO_FINDES']:
        reglas_servicio['MANEJO_FINDES']['nivelacion_historica']['fecha_inicio'] = "2026-01-01"
else:
    # If not present at all, create it
    reglas_servicio['MANEJO_FINDES'] = {
        "activo": 1,
        "modo": "SOFT",
        "peso_soft": 10000,
        "por_disponibilidad": {
            "5": {"flr": 0, "completos": 2, "medios": 1},
            "4": {"flr": 0, "completos": 1, "medios": 1},
            "3": {"flr": 0, "completos": 1, "medios": 1},
            "2": {"flr": 0, "completos": 1, "medios": 1},
            "1": {"flr": 0, "completos": 1, "medios": 0}
        },
        "nivelacion_historica": {
            "activo": True,
            "tipo": "ANUAL",
            "fecha_inicio": "2026-01-01"
        }
    }

# 2. Correct PESO_EQUIDAD_FINDES_MENSUAL historical date
if 'PESO_EQUIDAD_FINDES_MENSUAL' in reglas_servicio:
    reglas_servicio['PESO_EQUIDAD_FINDES_MENSUAL']['activo'] = 1
    reglas_servicio['PESO_EQUIDAD_FINDES_MENSUAL']['fecha_inicio'] = "2026-01-01"

print("\n=== SIMULATED RULES ACTIVE ===")
print(f"  MANEJO_FINDES: {reglas_servicio.get('MANEJO_FINDES')}")
print(f"  PESO_EQUIDAD_FINDES_MENSUAL: {reglas_servicio.get('PESO_EQUIDAD_FINDES_MENSUAL')}")

# Load employees and turnos
ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)
ajustes_servicio = db_queries.cargar_ajustes_reglas_servicio(fecha_inicio, fecha_fin, servicio_id)
ajustes_reglas['__servicio__'] = ajustes_servicio

# We need to manually inject rules_servicio into the loaded rules because obtener_empleados calls cargar_historial, etc.
# But wait, data_loader uses q.cargar_reglas_personal, etc.
# To make sure our in-memory rules_servicio is used, we can temporarily monkey-patch db_queries.cargar_reglas_servicio
original_cargar_reglas_servicio = db_queries.cargar_reglas_servicio
db_queries.cargar_reglas_servicio = lambda sid: reglas_servicio

try:
    empleados = obtener_empleados(servicio_id, fecha_inicio, DIAS_DEL_BLOQUE)
    turnos_dict = obtener_turnos(servicio_id)
    historial_semana_previa = db_queries.cargar_guardias_previas(fecha_inicio, dias_atras=28, servicio_id=servicio_id)

    offset_dia = fecha_inicio_dt.weekday()

    print("\nConstruyendo modelo...")
    modelo, turnos, flr_tracker, ctx = construir_modelo(
        empleados, config_turnos, turnos_dict, demanda_req, ajustes_db,
        DIAS_DEL_BLOQUE, feriados_indices, offset_dia, num_semanas,
        reglas_servicio=reglas_servicio,
        ajustes_reglas_personal=ajustes_reglas,
        historial_semana_previa=historial_semana_previa,
        servicio_id=servicio_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        modo_debug=False,
        force_assumptions=False
    )

    print("Resolviendo modelo...")
    df_resultados, flrs_asignados, df_cat_semanas, infracciones = resolver_modelo(
        modelo, turnos, flr_tracker, empleados, DIAS_DEL_BLOQUE, feriados_indices, 
        fecha_inicio, offset_dia, config_turnos, ctx=ctx, max_time_in_seconds=100
    )

    if df_resultados is not None:
        print("\n=== RESULTADOS SIMULADOS (FINES DE SEMANA) ===")
        # Count weekend shifts
        counts = {}
        for _, row in df_resultados.iterrows():
            dt = datetime.datetime.strptime(row['Fecha'], "%Y-%m-%d")
            if dt.weekday() in (5, 6):
                counts.setdefault(row['Personal'], []).append((row['Fecha'], row['Turno']))
        
        personal = [e.nombre for e in empleados]
        for name in sorted(personal):
            w_shifts = counts.get(name, [])
            print(f"{name}: {len(w_shifts)} guardias en fin de semana")
            for f_str, turno in w_shifts:
                print(f"  - {f_str} ({turno})")
    else:
        print("¡El modelo resultó INVIABLE con las reglas simuladas!")

finally:
    db_queries.cargar_reglas_servicio = original_cargar_reglas_servicio
