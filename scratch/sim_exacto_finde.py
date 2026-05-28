import sqlite3
import json
import sys
import os
from datetime import datetime, date, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.data_loader import obtener_empleados, obtener_turnos
from database import queries as db_queries
import rule_engine as _re

conn = sqlite3.connect("cronograma_inteligente.db")
cur = conn.cursor()

# We simulate for July 2026 (cronograma 232)
fecha_inicio = "2026-07-01"
fecha_fin = "2026-07-31"
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
turnos_dict = obtener_turnos(servicio_id)
reglas_servicio = db_queries.cargar_reglas_servicio(servicio_id)
ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)

print(f"Loaded {len(empleados)} employees.")
print(f"Feriados indices: {feriados_indices}")
print(f"Offset dia: {offset_dia}")

mapa_dias = {"lunes": 0, "martes": 1, "miercoles": 2, "jueves": 3, "viernes": 4, "sabado": 5, "domingo": 6}

for emp in empleados:
    print(f"\n--- EMPLEADO: {emp.nombre} ---")
    params = _re.resolver_parametros_regla(
        'EXACTO_FINDE_Y_DIA', emp.nombre, fecha_inicio,
        reglas_servicio, emp.reglas, ajustes_reglas
    )
    if not _re.regla_existe(params) or _re.regla_suspendida(params):
        print("  Rule does not exist or is suspended.")
        continue

    # Leer modo y filtrar si no corresponde al modo_filtro actual
    modo = params.get('modo', 'HARD').upper()
    print(f"  Modo: {modo}, Params: {params}")

    dia_conf = params.get('dia_semana', 4)
    if isinstance(dia_conf, str):
        dia_str = dia_conf.lower().replace('é', 'e').replace('á', 'a').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
        dia_semana_target = mapa_dias.get(dia_str, 4)
    else:
        dia_semana_target = int(dia_conf)
    print(f"  Dia semana target: {dia_semana_target} ({dia_conf})")

    # Availability of weekends
    findes = {}
    for d in range(dias_del_bloque):
        fecha_d = fecha_inicio_dt + timedelta(days=d)
        # Is finde logic:
        is_f = ((d + offset_dia) % 7) >= 5 or d in feriados_indices
        if is_f:
            lunes = (fecha_d - timedelta(days=fecha_d.weekday())).isoformat()
            findes.setdefault(lunes, []).append(d)

    k = sum(1 for lunes, dias in findes.items() if any(d not in emp.dias_licencia for d in dias))
    print(f"  k (weekend availability): {k}")

    # Specific day availability
    k_dia = 0
    for d in range(dias_del_bloque):
        fecha_d = fecha_inicio_dt + timedelta(days=d)
        if fecha_d.weekday() == dia_semana_target:
            if d in emp.dias_licencia:
                print(f"    d={d} ({fecha_d}) in licencias")
                continue
            fecha_d_str = fecha_d.isoformat()
            p_franco = _re.resolver_parametros_regla('FRANCO_FORZADO', emp.nombre, fecha_d_str, reglas_servicio, emp.reglas, ajustes_reglas)
            if _re.regla_existe(p_franco) and not _re.regla_suspendida(p_franco):
                print(f"    d={d} ({fecha_d}) in franco forzado: {p_franco}")
                continue
            k_dia += 1
    print(f"  k_dia (specific day availability): {k_dia}")

    # Targets
    mapping_findes = params.get('findes_por_disponibilidad')
    if mapping_findes and isinstance(mapping_findes, dict):
        target_findes = mapping_findes.get(str(k), mapping_findes.get(k, 0))
    else:
        target_findes = 0

    mapping_dias = params.get('dias_por_disponibilidad')
    if mapping_dias and isinstance(mapping_dias, dict):
        target_dias = mapping_dias.get(str(k_dia), mapping_dias.get(k_dia, 0))
    else:
        target_dias = 0

    print(f"  Targets: findes={target_findes}, dias={target_dias}")

    # Check tiene_asig_fija_en_dia
    tiene_asig_fija_en_dia = False
    for d_check in range(dias_del_bloque):
        fecha_d_check = fecha_inicio_dt + timedelta(days=d_check)
        if fecha_d_check.weekday() != dia_semana_target:
            continue
        if d_check in emp.dias_licencia:
            continue
        fecha_check_str = fecha_d_check.isoformat()
        p_asig = _re.resolver_parametros_regla('ASIGNACION_FIJA', emp.nombre, fecha_check_str, reglas_servicio, emp.reglas, ajustes_reglas)
        if _re.regla_existe(p_asig) and not _re.regla_suspendida(p_asig):
            tiene_asig_fija_en_dia = True
            print(f"  ASIGNACION_FIJA found on {fecha_check_str}: {p_asig}")
            # Do NOT break so we can print all of them
            
    print(f"  tiene_asig_fija_en_dia: {tiene_asig_fija_en_dia}")

conn.close()
