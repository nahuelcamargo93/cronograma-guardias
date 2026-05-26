import sys
import os
sys.path.append(os.path.abspath("."))
from ortools.sat.python import cp_model
from database.data_loader import obtener_empleados, obtener_turnos
from database import queries as db_queries
from data import FECHA_INICIO, FECHA_FIN, FERIADOS, SERVICIO_ID
from datetime import datetime

fecha_inicio = FECHA_INICIO
fecha_fin = FECHA_FIN
servicio_id = SERVICIO_ID

fecha_inicio_dt = datetime.strptime(fecha_inicio, "%Y-%m-%d")
fecha_fin_dt = datetime.strptime(fecha_fin, "%Y-%m-%d")
total_dias = (fecha_fin_dt - fecha_inicio_dt).days + 1
num_semanas = (total_dias + 6) // 7

config_turnos, metadata_turnos_raw, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
    servicio_id=servicio_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
)
reglas_servicio_db = db_queries.cargar_reglas_servicio(servicio_id)
ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)
empleados = obtener_empleados(servicio_id, fecha_inicio, total_dias)
turnos_dict = obtener_turnos(servicio_id)
historial_semana_previa = db_queries.cargar_guardias_previas(fecha_inicio, dias_atras=28, servicio_id=servicio_id)
offset_dia = fecha_inicio_dt.weekday()

feriados_indices = []
for f_str in FERIADOS:
    f_dt = datetime.strptime(f_str, "%Y-%m-%d")
    delta = (f_dt - fecha_inicio_dt).days
    if 0 <= delta < total_dias:
        feriados_indices.append(delta)

from debug_imposibilidad import construir_modelo_test

args_modelo = (empleados, config_turnos, turnos_dict, demanda_req, ajustes_db, total_dias, feriados_indices, offset_dia, num_semanas, reglas_servicio_db, ajustes_reglas, historial_semana_previa, servicio_id)

print("Building Model A (No soft rules)...")
model_a = construir_modelo_test(*args_modelo, reglas_a_ignorar=['REGLAS_BLANDAS'])
proto_a = model_a.Proto()

print("Building Model B (With soft rules)...")
model_b = construir_modelo_test(*args_modelo)
proto_b = model_b.Proto()

print(f"Model A has {len(proto_a.constraints)} constraints, {len(proto_a.variables)} variables.")
print(f"Model B has {len(proto_b.constraints)} constraints, {len(proto_b.variables)} variables.")

# Print constraints added in Model B (from index len(proto_a.constraints) onwards)
added_constraints = proto_b.constraints[len(proto_a.constraints):]
print(f"\n--- Added {len(added_constraints)} constraints ---")

for idx, c in enumerate(added_constraints):
    c_idx = len(proto_a.constraints) + idx
    # Print basic details about the constraint
    c_type = c.WhichOneof('constraint')
    name = c.name if c.name else f"Constraint #{c_idx}"
    
    # We are interested in linear/harder constraints
    if c_type == 'linear':
        vars_in_c = list(c.linear.vars)
        coeffs = list(c.linear.coeffs)
        bounds = list(c.linear.domain)
        # Format: bounds[0] <= sum(coeffs[i]*vars[i]) <= bounds[1]
        expr = " + ".join(f"{coef}*v{var}" for var, coef in zip(vars_in_c, coeffs))
        if len(bounds) == 2:
            print(f"{name} (Linear): {bounds[0]} <= {expr} <= {bounds[1]}")
        elif len(bounds) == 4:
            print(f"{name} (Linear): {bounds[0]}..{bounds[1]} or {bounds[2]}..{bounds[3]} <= {expr}")
        else:
            print(f"{name} (Linear): Domain={bounds} <= {expr}")
    elif c_type == 'bool_or':
        print(f"{name} (BoolOr): {list(c.bool_or.literals)}")
    elif c_type == 'bool_and':
        print(f"{name} (BoolAnd): {list(c.bool_and.literals)}")
    elif c_type == 'int_max':
        print(f"{name} (IntMax): Target v{c.int_max.target} == max({list(c.int_max.vars)})")
    elif c_type == 'int_min':
        print(f"{name} (IntMin): Target v{c.int_min.target} == min({list(c.int_min.vars)})")
    else:
        print(f"{name} (Type={c_type})")
