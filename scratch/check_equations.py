import sys, os
sys.path.append(os.getcwd())

import sqlite3
import pandas as pd
from datetime import date, timedelta
from ortools.sat.python import cp_model
import database.queries as q
from database.data_loader import obtener_empleados, obtener_turnos
from main import construir_modelo

servicio_id = 1
fecha_inicio = "2026-08-01"
dias_del_bloque = 31

df = pd.DataFrame(q.obtener_personal_db(servicio_id))
df = q.cargar_datos_personales_bd(df)
reglas_servicio = q.cargar_reglas_servicio(servicio_id)
ajustes_reglas_personal = q.cargar_ajustes_reglas_personal(fecha_inicio, "2026-08-31")

empleados = obtener_empleados(servicio_id, fecha_inicio, dias_del_bloque)
turnos_dict = obtener_turnos(servicio_id)
config_oferta, turnos_info, demanda_req, ajustes_db = q.cargar_configuracion_turnos(servicio_id)
fecha_inicio_dt = date.fromisoformat(fecha_inicio)
offset_dia = fecha_inicio_dt.weekday()

feriados_indices = []
feriados_db = q.obtener_feriados(fecha_inicio, "2026-08-31", servicio_id=servicio_id)
for f_str in feriados_db:
    delta = (date.fromisoformat(f_str) - fecha_inicio_dt).days
    if 0 <= delta < dias_del_bloque:
        feriados_indices.append(delta)

# Camargo
emp_filtered = [e for e in empleados if e.nombre == 'Camargo, Nahuel']

# Excluir todas las reglas excepto las básicas
from restricciones.hard import REGLAS_HARD
from restricciones.double import REGLAS_DOUBLE
codigos_basicos = ["LICENCIAS", "FRANCO_FORZADO", "EXCLUIR_TURNOS", "ASIGNACION_FIJA_OBLIGATORIA", "FINDE_LARGO_REGLAMENTARIO"]
exclusiones = set((r.rsplit('.', 1)[-1].upper(), None) for r in REGLAS_HARD + REGLAS_DOUBLE if r.rsplit('.', 1)[-1].upper() not in codigos_basicos)

modelo, turnos, flr_tracker, ctx = construir_modelo(
    emp_filtered, config_oferta, turnos_dict, demanda_req, ajustes_db,
    dias_del_bloque, feriados_indices, offset_dia, 6,
    reglas_servicio=reglas_servicio,
    ajustes_reglas_personal=ajustes_reglas_personal,
    historial_semana_previa={},
    servicio_id=servicio_id,
    fecha_inicio=fecha_inicio,
    fecha_fin="2026-08-31",
    modo_debug=False,
    force_assumptions=True,
    exclusiones=exclusiones
)

print("=== SEARCHING CONSTRAINTS INVOLVING VARS ===")
# Find indices of variables of interest
proto = modelo.Proto()
vars_of_interest = {}
for idx, v in enumerate(proto.variables):
    # Check if this variable is of interest:
    # 1. name contains 'REG_EXCLUIR_TURNOS__Camargo,_Nahuel_d9_Noche'
    # 2. name contains 'REG_ASIGNACION_FIJA_OBLIGATORIA__Camargo,_Nahuel_d9_Tarde_especial'
    # 3. name contains 'turno_Camargo,_Nahuel_dia9_Tarde_especial' or 'turno_Camargo,_Nahuel_dia9_Noche'
    # 4. name contains 'post_ok_jd_Camargo,_Nahuel_d5'
    if 'REG_EXCLUIR_TURNOS__Camargo' in v.name and 'd9_Noche' in v.name:
        vars_of_interest[idx] = v.name
    elif 'REG_ASIGNACION_FIJA_OBLIGATORIA__Camargo' in v.name and 'd9_Tarde_especial' in v.name:
        vars_of_interest[idx] = v.name
    elif 'turno_Camargo' in v.name and 'dia9_Tarde_especial' in v.name:
        vars_of_interest[idx] = v.name
    elif 'turno_Camargo' in v.name and 'dia9_Noche' in v.name:
        vars_of_interest[idx] = v.name
    elif 'post_ok_jd_Camargo' in v.name and 'd5' in v.name:
        vars_of_interest[idx] = v.name

for idx, name in vars_of_interest.items():
    print(f"Var {idx}: {name}")

for c_idx, c in enumerate(proto.constraints):
    involved = []
    # Collect all variables in constraint
    vars_in_c = list(c.linear.vars) if c.linear else []
    vars_in_c.extend(list(c.bool_and.literals) if c.bool_and else [])
    vars_in_c.extend(list(c.bool_or.literals) if c.bool_or else [])
    vars_in_c.extend(list(c.enforcement_literal) if c.enforcement_literal else [])
    
    for v_idx in vars_in_c:
        actual_idx = v_idx if v_idx >= 0 else -v_idx - 1
        if actual_idx in vars_of_interest:
            involved.append(vars_of_interest[actual_idx])
            
    if involved:
        print(f"\nConstraint {c_idx} (enforced by {list(c.enforcement_literal)}): involved={involved}")
        print(c)
