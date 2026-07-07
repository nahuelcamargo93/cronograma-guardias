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
from restricciones.cargador import reportar_conflicto

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

# Queremos investigar sólo a 'Camargo, Nahuel'
emp_filtered = [e for e in empleados if e.nombre == 'Camargo, Nahuel']

# Vamos a encender progresivamente las reglas para ver exactamente cuál choca con FLR
from restricciones.hard import REGLAS_HARD
from restricciones.double import REGLAS_DOUBLE

# Reglas básicas + FLR
codigos_basicos = ["LICENCIAS", "FRANCO_FORZADO", "EXCLUIR_TURNOS", "ASIGNACION_FIJA_OBLIGATORIA", "FINDE_LARGO_REGLAMENTARIO"]

codigos_reglas = []
for r in REGLAS_HARD + REGLAS_DOUBLE:
    cod = r.rsplit('.', 1)[-1].upper()
    if cod not in codigos_basicos:
        codigos_reglas.append(cod)

# Empezamos solo con las básicas
exclusiones = set((cod, None) for cod in codigos_reglas)

print("Building model with ONLY basic rules + FLR...")
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

solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 10
status = solver.Solve(modelo)

if status == cp_model.INFEASIBLE:
    print("Model is INFEASIBLE with ONLY basic rules!")
    reportar_conflicto(solver, ctx)
else:
    print(f"Model is FEASIBLE with basic rules (status={status}). Let's add other rules one by one...")
    # Agregar las otras reglas de una en una
    for cod in codigos_reglas:
        print(f"Testing with rule {cod} enabled...")
        excl = set((c, None) for c in codigos_reglas if c != cod)
        modelo_test, _, _, ctx_test = construir_modelo(
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
            exclusiones=excl
        )
        status_test = solver.Solve(modelo_test)
        if status_test == cp_model.INFEASIBLE:
            print(f"--> Rule {cod} causes INFEASIBILITY!")
            reportar_conflicto(solver, ctx_test)
            break
