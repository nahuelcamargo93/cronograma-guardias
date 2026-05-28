import sqlite3
import json
from datetime import datetime, date, timedelta

# Add root folder to sys.path
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.data_loader import obtener_empleados, obtener_turnos
from database import queries as db_queries
import rule_engine as _re

fecha_inicio = "2027-07-01"
fecha_fin = "2027-07-31"
servicio_id = 3

fecha_inicio_dt = date.fromisoformat(fecha_inicio)
fecha_fin_dt = date.fromisoformat(fecha_fin)
dias_del_bloque = (fecha_fin_dt - fecha_inicio_dt).days + 1

from data import FERIADOS
feriados_indices = []
for f_str in FERIADOS:
    f_dt = date.fromisoformat(f_str)
    if fecha_inicio_dt <= f_dt <= fecha_fin_dt:
        feriados_indices.append((f_dt - fecha_inicio_dt).days)

offset_dia = fecha_inicio_dt.weekday()

empleados = obtener_empleados(servicio_id, fecha_inicio, dias_del_bloque)
reglas_servicio = db_queries.cargar_reglas_servicio(servicio_id)
ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)

ajustes_servicio = db_queries.cargar_ajustes_reglas_servicio(fecha_inicio, fecha_fin, servicio_id)
ajustes_reglas['__servicio__'] = ajustes_servicio

print(f"Total employees: {len(empleados)}")

planta_total_target = 0
residente_total_target = 0

mapa_dias = {"lunes": 0, "martes": 1, "miercoles": 2, "jueves": 3, "viernes": 4, "sabado": 5, "domingo": 6}

for emp in empleados:
    # Check what role they have
    # If they are Planta or Residente. Wait, role is emp.rol, and enabled puestos is emp.puestos_habilitados
    role = emp.rol
    puestos = list(emp.puestos_habilitados)
    
    # Resolve EXACTO_FINDE_Y_DIA
    params = _re.resolver_parametros_regla(
        'EXACTO_FINDE_Y_DIA', emp.nombre, fecha_inicio,
        reglas_servicio, emp.reglas, ajustes_reglas
    )
    if not _re.regla_existe(params) or _re.regla_suspendida(params):
        print(f"{emp.nombre} ({role}): Rule not exists or suspended")
        continue

    dia_conf = params.get('dia_semana', 4)
    if isinstance(dia_conf, str):
        dia_str = dia_conf.lower().replace('é', 'e').replace('á', 'a').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
        dia_semana_target = mapa_dias.get(dia_str, 4)
    else:
        dia_semana_target = int(dia_conf)

    # Specific day availability (Friday)
    k_dia = 0
    for d in range(dias_del_bloque):
        fecha_d = fecha_inicio_dt + timedelta(days=d)
        if fecha_d.weekday() == dia_semana_target:
            if d in emp.dias_licencia:
                continue
            fecha_d_str = fecha_d.isoformat()
            p_franco = _re.resolver_parametros_regla('FRANCO_FORZADO', emp.nombre, fecha_d_str, reglas_servicio, emp.reglas, ajustes_reglas)
            if _re.regla_existe(p_franco) and not _re.regla_suspendida(p_franco):
                continue
            k_dia += 1

    mapping_dias = params.get('dias_por_disponibilidad')
    target_dias = mapping_dias.get(str(k_dia), mapping_dias.get(k_dia, 0)) if mapping_dias else 0
    
    # Print target
    print(f"{emp.nombre} ({role}): k_dia={k_dia}, target_dias={target_dias}, puestos_habilitados={puestos}")
    
    if "Planta" in puestos or (not puestos and role == "Planta"):
        planta_total_target += target_dias
    elif "Residente" in puestos or (not puestos and role == "Residente"):
        residente_total_target += target_dias
    else:
        # If no role or multiple, let's see
        print(f"Warning: {emp.nombre} has unknown/mixed role: {role}, puestos: {puestos}")

print(f"\nTOTAL TARGETS:")
print(f"Planta: Sum of Friday targets = {planta_total_target}")
print(f"Residente: Sum of Friday targets = {residente_total_target}")
