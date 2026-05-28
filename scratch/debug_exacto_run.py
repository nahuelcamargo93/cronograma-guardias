import sqlite3
import json
import sys
import os
from datetime import datetime, date, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.data_loader import obtener_empleados, obtener_turnos
from database import queries as db_queries
from main import construir_modelo
from data import FERIADOS, FECHA_INICIO, FECHA_FIN, SERVICIO_ID
import rule_engine as _re

fecha_inicio = "2026-07-01"
fecha_fin = "2026-07-31"
servicio_id = 3

fecha_inicio_dt = date.fromisoformat(fecha_inicio)
fecha_fin_dt = date.fromisoformat(fecha_fin)
dias_del_bloque = (fecha_fin_dt - fecha_inicio_dt).days + 1
num_semanas = (dias_del_bloque + 6) // 7

feriados_indices = []
for f_str in FERIADOS:
    f_dt = date.fromisoformat(f_str)
    if fecha_inicio_dt <= f_dt <= fecha_fin_dt:
        feriados_indices.append((f_dt - fecha_inicio_dt).days)

offset_dia = fecha_inicio_dt.weekday()

config_turnos, metadata_turnos_raw, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
    servicio_id=servicio_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
)
reglas_servicio_db = db_queries.cargar_reglas_servicio(servicio_id)
ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)

ajustes_servicio = db_queries.cargar_ajustes_reglas_servicio(fecha_inicio, fecha_fin, servicio_id)
ajustes_reglas['__servicio__'] = ajustes_servicio

empleados = obtener_empleados(servicio_id, fecha_inicio, dias_del_bloque)
turnos_dict = obtener_turnos(servicio_id)
historial_semana_previa = db_queries.cargar_guardias_previas(fecha_inicio, dias_atras=28, servicio_id=servicio_id)

# Build a mock CpModel and turnos vars
from ortools.sat.python import cp_model
modelo = cp_model.CpModel()
turnos_vars = {}

for emp in empleados:
    nombre = emp.nombre
    for dia in range(dias_del_bloque):
        es_finde = ((dia + offset_dia) % 7) >= 5 or dia in feriados_indices
        tipo_dia = "Finde_Feriado" if es_finde else "Semana"
        lista_turnos = config_turnos.get(tipo_dia, {}).keys()
        for t in lista_turnos:
            turnos_vars[(nombre, dia, t)] = modelo.NewBoolVar(f'turno_{nombre}_dia{dia}_{t}')

# Let's run a modified version of _aplicar_exacto_finde_y_dia and print everything
from hard_rules import _is_finde

mapa_dias = {"lunes": 0, "martes": 1, "miercoles": 2, "jueves": 3, "viernes": 4, "sabado": 5, "domingo": 6}

print("Running manual _aplicar_exacto_finde_y_dia simulation:")
for emp in empleados:
    params = _re.resolver_parametros_regla(
        'EXACTO_FINDE_Y_DIA', emp.nombre, FECHA_INICIO,
        reglas_servicio_db, emp.reglas, ajustes_reglas
    )
    if not _re.regla_existe(params) or _re.regla_suspendida(params):
        print(f"[{emp.nombre}] Rule doesn't exist or suspended")
        continue

    # Leer modo y filtrar si no corresponde al modo_filtro actual
    modo = params.get('modo', 'HARD').upper()
    print(f"[{emp.nombre}] Modo: {modo}")

    # --- 1. CONFIGURACIÓN DÍA DE LA SEMANA ---
    dia_conf = params.get('dia_semana', 4)
    if isinstance(dia_conf, str):
        dia_str = dia_conf.lower().replace('é', 'e').replace('á', 'a').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
        dia_semana_target = mapa_dias.get(dia_str, 4)
    else:
        dia_semana_target = int(dia_conf)

    # --- 2. CÁLCULO DE DISPONIBILIDAD DE FINES DE SEMANA ---
    findes = {}
    for d in range(dias_del_bloque):
        fecha_d = fecha_inicio_dt + timedelta(days=d)
        if _is_finde(d, offset_dia, feriados_indices):
            lunes = (fecha_d - timedelta(days=fecha_d.weekday())).isoformat()
            findes.setdefault(lunes, []).append(d)

    k = sum(1 for lunes, dias in findes.items() if any(d not in emp.dias_licencia for d in dias))

    # --- 3. CÁLCULO DE DISPONIBILIDAD DEL DÍA ESPECÍFICO ---
    k_dia = 0
    for d in range(dias_del_bloque):
        fecha_d = fecha_inicio_dt + timedelta(days=d)
        if fecha_d.weekday() == dia_semana_target:
            if d in emp.dias_licencia:
                continue
            fecha_d_str = fecha_d.isoformat()
            p_franco = _re.resolver_parametros_regla('FRANCO_FORZADO', emp.nombre, fecha_d_str, reglas_servicio_db, emp.reglas, ajustes_reglas)
            if _re.regla_existe(p_franco) and not _re.regla_suspendida(p_franco):
                continue
            k_dia += 1

    # --- 4. OBTENER TARGETS ---
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

    # --- 5. APLICAR LÓGICA DE FINES DE SEMANA ---
    vars_findes = []
    for lunes, dias in findes.items():
        dias_habilitados = []
        for d in dias:
            if d in emp.dias_licencia:
                continue
            fecha_d_str = (fecha_inicio_dt + timedelta(days=d)).isoformat()
            p_franco = _re.resolver_parametros_regla('FRANCO_FORZADO', emp.nombre, fecha_d_str, reglas_servicio_db, emp.reglas, ajustes_reglas)
            if _re.regla_existe(p_franco) and not _re.regla_suspendida(p_franco):
                continue
            dias_habilitados.append(d)
        
        if not dias_habilitados:
            continue
        
        v_este_finde = modelo.NewBoolVar(f'traba_f_exacto_finde_dia_{emp.nombre}_{lunes}')
        pool_f = []
        for d in dias_habilitados:
            for td in ["Finde_Feriado"]:
                for t in config_turnos.get(td, {}).keys():
                    if (emp.nombre, d, t) in turnos_vars:
                        pool_f.append(turnos_vars[(emp.nombre, d, t)])
        
        if pool_f:
            modelo.AddMaxEquality(v_este_finde, pool_f)
            vars_findes.append(v_este_finde)

    target_f_real = min(target_findes, len(vars_findes)) if vars_findes else 0
    print(f"  vars_findes count: {len(vars_findes)}, target_f_real: {target_f_real}")

    if vars_findes:
        if modo == "HARD":
            modelo.Add(sum(vars_findes) == target_f_real)

    # --- 6. APLICAR LÓGICA DE DÍA ESPECÍFICO ---
    tiene_asig_fija_en_dia = False
    for d_check in range(dias_del_bloque):
        fecha_d_check = fecha_inicio_dt + timedelta(days=d_check)
        if fecha_d_check.weekday() != dia_semana_target:
            continue
        if d_check in emp.dias_licencia:
            continue
        fecha_check_str = fecha_d_check.isoformat()
        p_asig = _re.resolver_parametros_regla('ASIGNACION_FIJA', emp.nombre, fecha_check_str, reglas_servicio_db, emp.reglas, ajustes_reglas)
        if _re.regla_existe(p_asig) and not _re.regla_suspendida(p_asig):
            tiene_asig_fija_en_dia = True
            print(f"  ASIGNACION_FIJA found on {fecha_check_str} for {emp.nombre}")
            break

    print(f"  tiene_asig_fija_en_dia: {tiene_asig_fija_en_dia}")
    if not tiene_asig_fija_en_dia:
        vars_dia = []
        for d in range(dias_del_bloque):
            fecha_d = fecha_inicio_dt + timedelta(days=d)
            if fecha_d.weekday() != dia_semana_target:
                continue
            if d in emp.dias_licencia:
                continue
            fecha_d_str = fecha_d.isoformat()
            p_franco = _re.resolver_parametros_regla('FRANCO_FORZADO', emp.nombre, fecha_d_str, reglas_servicio_db, emp.reglas, ajustes_reglas)
            if _re.regla_existe(p_franco) and not _re.regla_suspendida(p_franco):
                continue

            v_este_dia = modelo.NewBoolVar(f'traba_dia_exacto_finde_dia_{emp.nombre}_{dia_semana_target}_{d}')
            pool_d = []
            for t in turnos_dict.keys():
                if (emp.nombre, d, t) in turnos_vars:
                    pool_d.append(turnos_vars[(emp.nombre, d, t)])

            if pool_d:
                modelo.AddMaxEquality(v_este_dia, pool_d)
                vars_dia.append(v_este_dia)

        target_d_real = min(target_dias, len(vars_dia)) if vars_dia else 0
        print(f"  vars_dia count: {len(vars_dia)}, target_d_real: {target_d_real}")

        if vars_dia:
            if modo == "HARD":
                modelo.Add(sum(vars_dia) == target_d_real)
                print(f"  Added HARD constraint: sum(vars_dia) == {target_d_real}")
