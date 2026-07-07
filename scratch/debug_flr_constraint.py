import sys, os
sys.path.append(os.getcwd())

import sqlite3
import pandas as pd
from datetime import date, timedelta
from ortools.sat.python import cp_model
import traceback

original_add = cp_model.CpModel.add

added_constraints = []
def my_add(self, constraint):
    res = original_add(self, constraint)
    stack = traceback.format_stack()
    added_constraints.append((constraint, res, stack))
    return res
cp_model.CpModel.add = my_add
cp_model.CpModel.Add = my_add

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

import database.queries as q
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

print("=== PRINTING STACK TRACES OF EMPTY CONSTRAINTS ===")
proto = modelo.Proto()
for c, wrapper, stack in added_constraints:
    c_proto = proto.constraints[wrapper.Index()]
    is_empty_or = c_proto.bool_or and len(c_proto.bool_or.literals) == 0
    is_empty_and = c_proto.bool_and and len(c_proto.bool_and.literals) == 0
    # Wait, check if it's actually empty bool_or or bool_and
    if (c_proto.HasField('bool_or') and len(c_proto.bool_or.literals) == 0) or (c_proto.HasField('bool_and') and len(c_proto.bool_and.literals) == 0):
        print(f"Empty Constraint Index {wrapper.Index()} (enforced by {list(c_proto.enforcement_literal)}):")
        print("".join(stack))
        print("-"*50)
