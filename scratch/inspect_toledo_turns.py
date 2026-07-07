import sys, os
sys.path.append(os.getcwd())

import sqlite3
import pandas as pd
from datetime import date
import database.queries as q
from database.data_loader import obtener_empleados, obtener_turnos
from main import construir_modelo

servicio_id = 1
fecha_inicio = "2026-08-01"
dias_del_bloque = 31

df = pd.DataFrame(q.obtener_personal_db(servicio_id))
df = q.cargar_datos_personales_bd(df)
historial = q.cargar_historial(df, fecha_inicio)
reglas_db = q.cargar_reglas_personal(servicio_id)
reglas_rol_db = q.cargar_reglas_rol(servicio_id)
reglas_servicio = q.cargar_reglas_servicio(servicio_id)
ajustes_reglas_personal = q.cargar_ajustes_reglas_personal(fecha_inicio, "2026-08-31")

empleados = obtener_empleados(servicio_id, fecha_inicio, dias_del_bloque)
turnos_dict = obtener_turnos(servicio_id)
config_oferta, _, demanda_req, ajustes_db = q.cargar_configuracion_turnos(servicio_id, fecha_inicio, "2026-08-31")
feriados_indices = []
offset_dia = date.fromisoformat(fecha_inicio).weekday()
num_semanas = 5

modelo, turnos, flr_tracker, ctx = construir_modelo(
    empleados, config_oferta, turnos_dict, demanda_req, ajustes_db,
    dias_del_bloque, feriados_indices, offset_dia, num_semanas,
    reglas_servicio=reglas_servicio,
    ajustes_reglas_personal=ajustes_reglas_personal,
    fecha_inicio=fecha_inicio,
    fecha_fin="2026-08-31"
)

emp = next(e for e in empleados if e.nombre == 'Toledo, Andrea')
d = 24
dia_semana = (d + offset_dia) % 7

print("=== Toledo's Turnos in ctx.turnos on Day 24 ===")
for k in ctx.turnos.keys():
    if k[0] == emp.nombre and k[1] == d:
        print(k)

print("\n=== Simulating excluir_turnos.py for Toledo on Day 24 ===")
import rule_engine as _re
fecha_d = (date.fromisoformat(fecha_inicio) + timedelta(days=d)).isoformat() if 'timedelta' in globals() else "2026-08-25"
params = _re.resolver_parametros_regla(
    'EXCLUIR_TURNOS', emp.nombre, fecha_d,
    ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
)
print("EXCLUIR_TURNOS params:", params)
for excl in params:
    if dia_semana not in excl.get('dias', list(range(7))):
        print(f"Skipping excl {excl} because dia_semana {dia_semana} not in {excl.get('dias')}")
        continue
    for tp in excl.get('turnos', []):
        key = (emp.nombre, d, tp)
        in_turnos = key in ctx.turnos
        print(f"Checking tp: '{tp}' | key: {key} | in ctx.turnos: {in_turnos}")
