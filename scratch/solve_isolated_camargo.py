import sys, os
sys.path.append(os.getcwd())

import sqlite3
import pandas as pd
from datetime import date, timedelta
from ortools.sat.python import cp_model
import rule_engine as _re
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

# Force quantity_req to 0 in rules to avoid the quantity conflict itself
reglas_servicio['FINDE_LARGO_REGLAMENTARIO']['por_disponibilidad'] = {"5": 0, "4": 0, "3": 0, "2": 0, "1": 0}

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

# Camargo, Nahuel
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

# Force the FLR at d=5 to be 1
v_flr = flr_tracker[("Camargo, Nahuel", 5)]
modelo.Add(v_flr == 1)

# Solve with assumptions
modelo.ClearAssumptions()
modelo.AddAssumptions([b for _, b in ctx.assumptions])

solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 10
status = solver.Solve(modelo)

print("Solver status with forced FLR d=5:", solver.StatusName(status))
if status == cp_model.INFEASIBLE:
    conflict = solver.SufficientAssumptionsForInfeasibility()
    print("Conflict assumptions indices:", list(conflict))
    for lit in conflict:
        var_idx = lit if lit >= 0 else -lit - 1
        for name, var in ctx.assumptions:
            if var.Index() == var_idx:
                print(f"Conflicting rule: {name}")
