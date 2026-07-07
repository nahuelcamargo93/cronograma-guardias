import sys, os
sys.path.append(os.getcwd())

import sqlite3
import pandas as pd
from datetime import date, timedelta
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

# Find Toledo variable
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
            domain = list(c.linear.domain)
            enforcements = []
            for lit in c.enforcement_literal:
                v_i = lit if lit >= 0 else -lit - 1
                v_name = proto.variables[v_i].name
                sign = "+" if lit >= 0 else "-"
                enforcements.append(f"{sign}{v_name}")
            
            vars_and_coeffs = list(zip(c.linear.vars, c.linear.coeffs))
            other_vars = [f"{coef}*{proto.variables[v_i].name}" for v_i, coef in vars_and_coeffs]
            
            # Print only if it forces variable to 0 (i.e. domain is [0, 0] or equivalent and it is the only variable, or is a bound)
            if domain == [0, 0] and len(c.linear.vars) == 1:
                print(f"\nConstraint {c_idx} (Forces to 0):")
                print(f"  Enforced by: {enforcements}")
                print(f"  Expression: {' + '.join(other_vars)}")

print("\n=== Toledo's Exclusions from resolver_parametros_regla ===")
import rule_engine as _re
emp = next(e for e in empleados if e.nombre == 'Toledo, Andrea')
for d in range(dias_del_bloque):
    fecha_d = (date.fromisoformat(fecha_inicio) + timedelta(days=d)).isoformat()
    params = _re.resolver_parametros_regla(
        'EXCLUIR_TURNOS', emp.nombre, fecha_d,
        reglas_servicio, emp.reglas, ajustes_reglas_personal
    )
    if _re.regla_existe(params):
        # Print if there is any parameter
        print(f"Day {d} ({fecha_d}): {params}")
