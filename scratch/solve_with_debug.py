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

print("post_ok_jd_Camargo_d5 value:", solver.Value(var_wrapper))
neg_var_idx = next(idx for idx, v in enumerate(proto.variables) if 'post_ok_jd_Camargo' in v.name and 'd5_negated' in v.name)
print("post_ok_jd_Camargo_d5_negated value:", solver.Value(cp_model.BoolVarT(modelo, neg_var_idx, proto.variables[neg_var_idx].name)))

# Print sum of vars_post
vars_post_indices = list(range(74, 84))
vars_post_sum = sum(solver.Value(cp_model.BoolVarT(modelo, i, proto.variables[i].name)) for i in vars_post_indices)
print("sum(vars_post) value:", vars_post_sum)
for i in vars_post_indices:
    print(f"  {proto.variables[i].name} = {solver.Value(cp_model.BoolVarT(modelo, i, proto.variables[i].name))}")
