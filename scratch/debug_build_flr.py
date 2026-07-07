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

# Camargo
emp = next(e for e in empleados if e.nombre == 'Camargo, Nahuel')

# Let's inspect what is in vars_post for d=5 in the actual build logic:
d = 5
d_post = d + 4
es_f_po = ((d_post + offset_dia) % 7 >= 5) or (d_post in feriados_indices)
tipo_d = 'Finde_Feriado' if es_f_po else 'Semana'

print("d_post:", d_post)
print("es_f_po:", es_f_po)
print("tipo_d:", tipo_d)
print("Keys in demanda_turnos:", list(config_oferta.get(tipo_d, {}).keys()))

# Build the model variables like main.py does
modelo = cp_model.CpModel()
turnos = {}
for e in [emp]:
    for dia in range(dias_del_bloque):
        es_finde = ((dia + offset_dia) % 7) >= 5 or dia in feriados_indices
        tipo_dia_res = "Finde_Feriado" if es_finde else "Semana"
        tipos_turnos = config_oferta.get(tipo_dia_res, {}).keys()
        for t in tipos_turnos:
            # Let's see if the variable is created
            t_config = config_oferta.get(tipo_dia_res, {}).get(t, {})
            dias_hab_str = t_config.get("Dias_Habilitados", "0,1,2,3,4,5,6")
            dias_permitidos = {int(x) for x in dias_hab_str.split(",") if x.strip().isdigit()}
            dia_semana_actual = (dia + offset_dia) % 7
            
            if es_finde:
                if not (5 in dias_permitidos or 6 in dias_permitidos): continue
            else:
                if dia_semana_actual not in dias_permitidos: continue
                
            t_info = turnos_dict.get(t)
            puesto_nombre_turno = t_info.puesto_nombre if t_info else None
            if puesto_nombre_turno and puesto_nombre_turno not in e.puestos_habilitados:
                continue
                
            turnos[(e.nombre, dia, t)] = modelo.NewBoolVar(f"turno_{e.nombre}_dia{dia}_{t}")

vars_post = [
    turnos[(emp.nombre, d_post, t)]
    for t in config_oferta.get(
        'Finde_Feriado' if es_f_po else 'Semana', {}
    ).keys()
    if (emp.nombre, d_post, t) in turnos
]

print("vars_post created in debug:")
for v in vars_post:
    print(f"  {v.Name()} (index={v.Index()})")
