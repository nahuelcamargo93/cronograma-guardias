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

# Force post_ok_jd_Camargo,_Nahuel_d5 to 1
proto = modelo.Proto()
var_idx = next(idx for idx, v in enumerate(proto.variables) if 'post_ok_jd_Camargo' in v.name and 'd5' in v.name)
var_wrapper = cp_model.BoolVar(modelo.Proto(), var_idx)
modelo.Add(var_wrapper == 1)

# Now, we find the minimal unsatisfiable set of constraints
num_constraints = len(proto.constraints)
print(f"Total constraints: {num_constraints}")

# Let's verify it is indeed infeasible first
solver = cp_model.CpSolver()
status = solver.Solve(modelo)
print("Initial status:", solver.StatusName(status))
assert status == cp_model.INFEASIBLE

essential_indices = []
# We will iterate through all constraints, and try to remove each one.
# If the model becomes feasible, then that constraint is essential!
for c_idx in range(num_constraints):
    # Copy the proto
    from ortools.sat.cp_model_pb2 import CpModelProto
    proto_copy = CpModelProto()
    proto_copy.CopyFrom(modelo.Proto())
    
    # We clear the constraints, and add all except c_idx
    proto_copy.ClearField('constraints')
    for i, c in enumerate(modelo.Proto().constraints):
        if i != c_idx:
            proto_copy.constraints.add().CopyFrom(c)
            
    # Solve
    dummy_model = cp_model.CpModel()
    dummy_model.Proto().CopyFrom(proto_copy)
    
    status = solver.Solve(dummy_model)
    if status == cp_model.FEASIBLE or status == cp_model.OPTIMAL:
        essential_indices.append(c_idx)
        print(f"Constraint {c_idx} is ESSENTIAL!")
        print(modelo.Proto().constraints[c_idx])
        # Find which variables are in this constraint
        c = modelo.Proto().constraints[c_idx]
        involved_vars = []
        if c.linear:
            involved_vars.extend(list(c.linear.vars))
        if c.bool_or:
            involved_vars.extend(list(c.bool_or.literals))
        if c.bool_and:
            involved_vars.extend(list(c.bool_and.literals))
        involved_vars.extend(list(c.enforcement_literal))
        for v_idx in set(involved_vars):
            v_idx_actual = v_idx if v_idx >= 0 else -v_idx - 1
            print(f"  Var {v_idx_actual}: {modelo.Proto().variables[v_idx_actual].name}")
        print("-" * 50)
