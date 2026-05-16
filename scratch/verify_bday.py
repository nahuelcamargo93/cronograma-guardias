import pandas as pd
from datetime import date, timedelta
from ortools.sat.python import cp_model
from hard_rules import aplicar_reglas_duras
from models import Empleado, Turno

# Mock data
FECHA_INICIO = "2026-06-01"
DIAS_DEL_BLOQUE = 30

# Alcaraz has birthday on June 15
emp = Empleado(
    nombre="ALCARAZ FRANCISO",
    rol="Medico",
    es_padre=False,
    fecha_cumpleanos="1985-06-15",
    dias_licencia=set()
)

empleados = [emp]
turnos_dict = {"G": Turno(nombre="G", horas=24, puesto_nombre="Medico")}
demanda_turnos = {"Semana": {"G": {}}, "Finde_Feriado": {"G": {}}}
demanda_req = {"Semana": [], "Finde_Feriado": []}
ajustes_demanda = {}
feriados = []
offset_dia = 0 
num_semanas = 5
reglas_servicio = {
    'MAX_HORAS_SEMANA': {'limite': 100},
    'CUMPLEANOS_LIBRE': {}
}

modelo = cp_model.CpModel()
vars = {}
for d in range(DIAS_DEL_BLOQUE):
    vars[("ALCARAZ FRANCISO", d, "G")] = modelo.NewBoolVar(f"t_{d}")

modelo.Maximize(sum(vars.values()))

aplicar_reglas_duras(
    modelo, vars, empleados, demanda_turnos, turnos_dict,
    demanda_req, ajustes_demanda, DIAS_DEL_BLOQUE, feriados,
    offset_dia, num_semanas, {}, reglas_servicio, {}, 3
)

solver = cp_model.CpSolver()
status = solver.Solve(modelo)

if status == cp_model.OPTIMAL:
    bday_idx = 14 # June 15
    val = solver.Value(vars[("ALCARAZ FRANCISO", bday_idx, "G")])
    print(f"Assignment on Birthday (June 15, idx {bday_idx}): {val}")
    if val == 0:
        print("SUCCESS: Birthday rule applied!")
    else:
        print("FAILURE: Birthday rule NOT applied!")
else:
    print(f"Solver status: {status}")
