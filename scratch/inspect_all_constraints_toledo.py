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

print("=== CONSTRAINTS FOR TOLEDO ===")
for c_idx, c in enumerate(proto.constraints):
    if c.linear and len(c.linear.vars) > 0:
        # Check if any variable belongs to Toledo, Andrea
        toledo_vars = []
        for v in c.linear.vars:
            v_name = proto.variables[v].name
            if "Toledo, Andrea" in v_name:
                toledo_vars.append(v_name)
        
        if toledo_vars:
            # Check if this is a strict equality or bounds constraint
            domain = list(c.linear.domain)
            enforcements = []
            for lit in c.enforcement_literal:
                v_i = lit if lit >= 0 else -lit - 1
                v_name = proto.variables[v_i].name
                sign = "+" if lit >= 0 else "-"
                enforcements.append(f"{sign}{v_name}")
            
            # Print if it forces something to 1 or 0 (domain is [1,1] or [0,0] or similar)
            # Let's print all of them for now, but compactly
            vars_and_coeffs = [f"{coeff}*{proto.variables[v].name}" for v, coeff in zip(c.linear.vars, c.linear.coeffs)]
            if len(c.linear.vars) <= 2 and (domain in [[0,0], [1,1], [0,1]] or domain[1] == 0 or domain[0] == 1):
                print(f"C{c_idx}: Enforced by {enforcements} | {' + '.join(vars_and_coeffs)} in domain {domain}")

print("\n=== CONSTRAINTS FOR GARCIA ===")
for c_idx, c in enumerate(proto.constraints):
    if c.linear and len(c.linear.vars) > 0:
        garcia_vars = []
        for v in c.linear.vars:
            v_name = proto.variables[v].name
            if "Garcia, Luciano" in v_name:
                garcia_vars.append(v_name)
        
        if garcia_vars:
            domain = list(c.linear.domain)
            enforcements = []
            for lit in c.enforcement_literal:
                v_i = lit if lit >= 0 else -lit - 1
                v_name = proto.variables[v_i].name
                sign = "+" if lit >= 0 else "-"
                enforcements.append(f"{sign}{v_name}")
            
            vars_and_coeffs = [f"{coeff}*{proto.variables[v].name}" for v, coeff in zip(c.linear.vars, c.linear.coeffs)]
            if len(c.linear.vars) <= 2 and (domain in [[0,0], [1,1], [0,1]] or domain[1] == 0 or domain[0] == 1):
                print(f"C{c_idx}: Enforced by {enforcements} | {' + '.join(vars_and_coeffs)} in domain {domain}")
