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

# Buscar los constraints 4206 y 4207
proto = modelo.Proto()
for c_idx in [4206, 4207]:
    if c_idx < len(proto.constraints):
        c = proto.constraints[c_idx]
        print(f"\n=== Constraint {c_idx} ===")
        # Enforcement literals
        enforcements = []
        for lit in c.enforcement_literal:
            # literal can be negative
            var_idx = lit if lit >= 0 else -lit - 1
            var_name = proto.variables[var_idx].name
            sign = "+" if lit >= 0 else "-"
            enforcements.append(f"{sign}{var_name}")
        print(f"Enforced by: {enforcements}")
        
        # Linear expression
        # Linear expression
        if c.linear and len(c.linear.vars) > 0:
            vars_and_coeffs = list(zip(c.linear.vars, c.linear.coeffs))
            domain = list(c.linear.domain)
            terms = [f"{coef}*{proto.variables[v_idx].name}" for v_idx, coef in vars_and_coeffs]
            print(f"Expression: {' + '.join(terms)} in domain {domain}")
