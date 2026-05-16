import pandas as pd
from datetime import date, timedelta
from ortools.sat.python import cp_model
from hard_rules import aplicar_reglas_duras
from models import Empleado, Turno

# Mock data
FECHA_INICIO = "2026-06-01"
DIAS_DEL_BLOQUE = 30
DIA_DEL_PADRE = "2026-06-21"

# Alcaraz is a father
emp = Empleado(
    nombre="ALCARAZ FRANCISO",
    rol="Medico",
    es_padre=True,
    fecha_cumpleanos=None,
    dias_licencia=set()
)

empleados = [emp]
turnos_dict = {"G": Turno(nombre="G", horas=24, puesto_nombre="Medico")}
demanda_turnos = {"Semana": {"G": {}}, "Finde_Feriado": {"G": {}}}
demanda_req = {"Semana": [], "Finde_Feriado": []}
ajustes_demanda = {}
feriados = []
offset_dia = 0 # June 1 2026 is Monday
num_semanas = 5
reglas_servicio = {
    'MAX_HORAS_SEMANA': {'limite': 100},
    'DIA_MADRE_PADRE_LIBRE': {}
}

modelo = cp_model.CpModel()
vars = {}
for d in range(DIAS_DEL_BLOQUE):
    vars[("ALCARAZ FRANCISO", d, "G")] = modelo.NewBoolVar(f"t_{d}")

# We want him to work as much as possible to see if the rule stops him
modelo.Maximize(sum(vars.values()))

aplicar_reglas_duras(
    modelo, vars, empleados, demanda_turnos, turnos_dict,
    demanda_req, ajustes_demanda, DIAS_DEL_BLOQUE, feriados,
    offset_dia, num_semanas, {}, reglas_servicio, {}, 3
)

solver = cp_model.CpSolver()
status = solver.Solve(modelo)

if status == cp_model.OPTIMAL:
    d_padre_idx = (date.fromisoformat(DIA_DEL_PADRE) - date.fromisoformat(FECHA_INICIO)).days
    val = solver.Value(vars[("ALCARAZ FRANCISO", d_padre_idx, "G")])
    print(f"Assignment on Father's Day ({DIA_DEL_PADRE}, idx {d_padre_idx}): {val}")
    if val == 0:
        print("SUCCESS: Father's Day rule applied!")
    else:
        print("FAILURE: Father's Day rule NOT applied!")
else:
    print(f"Solver status: {status}")
