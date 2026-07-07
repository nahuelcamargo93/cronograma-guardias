import sys, os
sys.path.append(os.getcwd())

import sqlite3
import pandas as pd
from datetime import date
import database.queries as q
from database.data_loader import obtener_empleados, obtener_turnos
from main import construir_modelo

servicio_id = 1
fecha_inicio = "2026-08-01"
dias_del_bloque = 31

df = pd.DataFrame(q.obtener_personal_db(servicio_id))
df = q.cargar_datos_personales_bd(df)
historial = q.cargar_historial(df, fecha_inicio)
reglas_db = q.cargar_reglas_personal(servicio_id)
reglas_rol_db = q.cargar_reglas_rol(servicio_id)
reglas_servicio = q.cargar_reglas_servicio(servicio_id)
ajustes_reglas_personal = q.cargar_ajustes_reglas_personal(fecha_inicio, "2026-08-31")

empleados = obtener_empleados(servicio_id, fecha_inicio, dias_del_bloque)
turnos_dict = obtener_turnos(servicio_id)
config_oferta, _, demanda_req, ajustes_db = q.cargar_configuracion_turnos(servicio_id, fecha_inicio, "2026-08-31")
feriados_indices = []
offset_dia = date.fromisoformat(fecha_inicio).weekday()
num_semanas = 5

modelo, turnos, flr_tracker, ctx = construir_modelo(
    empleados, config_oferta, turnos_dict, demanda_req, ajustes_db,
    dias_del_bloque, feriados_indices, offset_dia, num_semanas,
    reglas_servicio=reglas_servicio,
    ajustes_reglas_personal=ajustes_reglas_personal,
    fecha_inicio=fecha_inicio,
    fecha_fin="2026-08-31"
)

proto = modelo.Proto()

# Encontrar índice de la variable
var_name = "turno_Toledo, Andrea_dia24_Mañana_UCO"
var_idx = None
for i, var in enumerate(proto.variables):
    if var.name == var_name:
        var_idx = i
        break

if var_idx is None:
    print(f"No se encontró la variable {var_name}")
    sys.exit(1)

print(f"=== Buscando todas las restricciones sobre {var_name} (índice {var_idx}) ===")
for c_idx, c in enumerate(proto.constraints):
    if c.linear and len(c.linear.vars) > 0:
        if var_idx in c.linear.vars:
            # Check if domain limits it to 0
            # E.g. if sum of vars == 0, domain is [0, 0]
            # Or if it's a bound like <= 0
            domain = list(c.linear.domain)
            enforcements = []
            for lit in c.enforcement_literal:
                v_i = lit if lit >= 0 else -lit - 1
                v_name = proto.variables[v_i].name
                sign = "+" if lit >= 0 else "-"
                enforcements.append(f"{sign}{v_name}")
            
            vars_and_coeffs = list(zip(c.linear.vars, c.linear.coeffs))
            other_vars = [f"{coef}*{proto.variables[v_i].name}" for v_i, coef in vars_and_coeffs]
            
            print(f"\nConstraint {c_idx}:")
            print(f"  Enforced by: {enforcements}")
            print(f"  Expression: {' + '.join(other_vars)} in domain {domain}")
