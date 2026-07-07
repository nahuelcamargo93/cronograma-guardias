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

def test_with_val(post_ok_val):
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
        force_assumptions=False,
        exclusiones=exclusiones
    )
    # Find post_ok_jd_Camargo,_Nahuel_d5
    proto = modelo.Proto()
    var_idx = next(idx for idx, v in enumerate(proto.variables) if 'post_ok_jd_Camargo' in v.name and 'd5' in v.name)
    var = modelo.Proto().variables[var_idx]
    
    # Force value
    # Since var is a proto variable, we can't call Add on it directly in python unless we wrap it or use model.Add
    # The python helper has NewBoolVar which returns a BoolVar wrapper.
    # We can just create a wrapper using cp_model.BoolVar(modelo.Proto(), var_idx)
    var_wrapper = cp_model.BoolVar(modelo.Proto(), var_idx)
    modelo.Add(var_wrapper == post_ok_val)
    
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 5
    status = solver.Solve(modelo)
    print(f"Status with post_ok == {post_ok_val}: {solver.StatusName(status)}")

test_with_val(1)
test_with_val(0)
