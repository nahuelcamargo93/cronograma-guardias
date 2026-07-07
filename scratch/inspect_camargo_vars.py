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

# Queremos investigar a 'Camargo, Nahuel'
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

import sys
with open('scratch/camargo_output.txt', 'w', encoding='utf-8') as f:
    f.write("=== VARIABLES FOR CAMARGO ===\n")
    for k, v in turnos.items():
        if k[0] == 'Camargo, Nahuel':
            f.write(f"Variable: {v.Name()} (index={v.Index()})\n")

    f.write("\n=== CONSTRAINTS IN MODEL ===\n")
    proto = modelo.Proto()
    for c_idx, c in enumerate(proto.constraints):
        vars_in_constraint = []
        if c.linear:
            for var_idx in c.linear.vars:
                for k, v in turnos.items():
                    if v.Index() == var_idx and k[0] == 'Camargo, Nahuel':
                        vars_in_constraint.append(v.Name())
        if c.bool_and:
            for lit in c.bool_and.literals:
                var_idx = lit if lit >= 0 else -lit - 1
                for k, v in turnos.items():
                    if v.Index() == var_idx and k[0] == 'Camargo, Nahuel':
                        vars_in_constraint.append(v.Name())
        if c.bool_or:
            for lit in c.bool_or.literals:
                var_idx = lit if lit >= 0 else -lit - 1
                for k, v in turnos.items():
                    if v.Index() == var_idx and k[0] == 'Camargo, Nahuel':
                        vars_in_constraint.append(v.Name())
        
        if vars_in_constraint:
            f.write(f"Constraint {c_idx} ({c.name}): {vars_in_constraint}\n")
            f.write(str(c) + "\n")
