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

# Buscar constraints sobre Toledo en d=24
print("=== Buscando variables y constraints para Toledo en d=24 ===")
var_idx = None
for i, var in enumerate(modelo.Proto().variables):
    if "Toledo" in var.name and "dia24" in var.name:
        print(f"Variable {var.name} con índice {i}")
        if "Mañana_UCO" in var.name:
            var_idx = i

if var_idx is not None:
    # Buscar si hay alguna restricción del tipo var_idx == 1
    found_c = False
    for c_idx, c in enumerate(modelo.Proto().constraints):
        if c.linear and len(c.linear.vars) > 0:
            # Check if it has the form: coeff * var == value
            # and contains var_idx
            if var_idx in c.linear.vars:
                # Print constraint details
                vars_and_coeffs = list(zip(c.linear.vars, c.linear.coeffs))
                domain = list(c.linear.domain)
                # print name of other variables
                other_names = [modelo.Proto().variables[v_i].name for v_i, _ in vars_and_coeffs]
                print(f"Constraint {c_idx}: {other_names} in domain {domain}")
                if len(vars_and_coeffs) == 1 and domain == [1, 1]:
                    print("  -> ¡Es una restricción de igualdad a 1!")
                    found_c = True
    if not found_c:
        print("  -> ¡No se encontró ninguna restricción de igualdad a 1!")
else:
    print(f"No se encontró la variable Mañana_UCO en d=24")
