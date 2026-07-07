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
    modo_debug=True,
    force_assumptions=False,
    exclusiones=exclusiones
)

# Force post_ok_jd_Camargo,_Nahuel_d5 to 1
proto = modelo.Proto()
var_idx = next(idx for idx, v in enumerate(proto.variables) if 'post_ok_jd_Camargo' in v.name and 'd5' in v.name)
var_wrapper = cp_model.BoolVarT(modelo, var_idx, proto.variables[var_idx].name)
modelo.Add(var_wrapper == 1)

solver = cp_model.CpSolver()
status = solver.Solve(modelo)

print("Solve status:", solver.StatusName(status))

# Check Constraint 949 (sum == 1) and 950 (sum != 1)
def check_constraint(c_idx):
    c = proto.constraints[c_idx]
    # Check enforcement
    is_active = True
    for lit in c.enforcement_literal:
        v_idx = lit if lit >= 0 else -lit - 1
        val = solver.Value(cp_model.BoolVarT(modelo, v_idx, proto.variables[v_idx].name))
        lit_val = val if lit >= 0 else (1 - val)
        if lit_val == 0:
            is_active = False
            break
            
    # Check linear expression value
    expr_val = 0
    if c.has_linear():
        for var, coeff in zip(c.linear.vars, c.linear.coeffs):
            val = solver.Value(cp_model.BoolVarT(modelo, var, proto.variables[var].name))
            expr_val += coeff * val
            
    # Check if expr_val is in domain
    in_domain = False
    if c.has_linear():
        domain = c.linear.domain
        for start, end in zip(domain[::2], domain[1::2]):
            if start <= expr_val <= end:
                in_domain = True
                break
                
    print(f"Constraint {c_idx} (active: {is_active}, expr_val: {expr_val}, in_domain: {in_domain}):")
    print(f"  Enforcement literals: {list(c.enforcement_literal)}")
    if c.has_linear():
        print(f"  Linear vars: {list(c.linear.vars)}")
        print(f"  Domain: {list(c.linear.domain)}")

check_constraint(949)
check_constraint(950)
check_constraint(951)
check_constraint(1717)
check_constraint(1718)
