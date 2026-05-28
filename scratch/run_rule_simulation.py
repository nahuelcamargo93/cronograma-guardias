import sys
import os
import datetime
from datetime import date, timedelta

# Add parent directory to path
sys.path.append(os.path.abspath('.'))

from data import FECHA_INICIO, FECHA_FIN, FERIADOS, SERVICIO_ID
from database import queries as db_queries
from database.data_loader import obtener_empleados, obtener_turnos
import rule_engine as _re

# Initialize licencias!
db_queries.init_licencias()

servicio_id = 3 # Medicos
fecha_inicio = "2026-06-01"
fecha_fin = "2026-06-30"

print(f"Service: {servicio_id}, Range: {fecha_inicio} to {fecha_fin}")

fecha_inicio_dt = date.fromisoformat(fecha_inicio)
fecha_fin_dt = date.fromisoformat(fecha_fin)
dias_del_bloque = (fecha_fin_dt - fecha_inicio_dt).days + 1
offset_dia = fecha_inicio_dt.weekday()

feriados_indices = []
for f_str in FERIADOS:
    f_dt = date.fromisoformat(f_str)
    delta = (f_dt - fecha_inicio_dt).days
    if 0 <= delta < dias_del_bloque:
        feriados_indices.append(delta)

findes = {}
for d_f in range(dias_del_bloque):
    fecha_df = fecha_inicio_dt + timedelta(days=d_f)
    dia_semana_f = (d_f + offset_dia) % 7
    es_finde_f = (dia_semana_f >= 5) or (d_f in feriados_indices)
    if es_finde_f:
        lunes_f = (fecha_df - timedelta(days=fecha_df.weekday())).isoformat()
        findes.setdefault(lunes_f, []).append(d_f)

empleados = obtener_empleados(servicio_id, fecha_inicio, dias_del_bloque)
reglas_servicio = db_queries.cargar_reglas_servicio(servicio_id)
ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)

mapa_dias = {"Lunes": 0, "Martes": 1, "Miercoles": 2, "Jueves": 3, "Viernes": 4, "Sabado": 5, "Domingo": 6}

print("\nSimulating rules for each employee:")
for emp in empleados:
    fecha_ini_str = fecha_inicio_dt.isoformat()
    params_min = _re.resolver_parametros_regla(
        'MIN_DIA_ESPECIFICO_MES', emp.nombre, fecha_ini_str,
        reglas_servicio, emp.reglas, ajustes_reglas
    )
    params_exacto = _re.resolver_parametros_regla(
        'EXACTO_DIA_ESPECIFICO_MES', emp.nombre, fecha_ini_str,
        reglas_servicio, emp.reglas, ajustes_reglas
    )
    
    has_min = _re.regla_existe(params_min) and not _re.regla_suspendida(params_min)
    has_exacto = _re.regla_existe(params_exacto) and not _re.regla_suspendida(params_exacto)
    
    # Si MIN_DIA_ESPECIFICO_MES está suspendida para este empleado, heredamos la suspensión a EXACTO_DIA_ESPECIFICO_MES
    if has_exacto and params_min is not None and _re.regla_suspendida(params_min):
        has_exacto = False
        
    if not has_min and not has_exacto:
        print(f"  {emp.nombre:30s}: rules not active (min: {has_min}, exact: {has_exacto})")
        continue
        
    is_exact = has_exacto
    params = params_exacto if has_exacto else params_min
        
    dia_conf = params.get('dia_semana', 4)
    if isinstance(dia_conf, str):
        dia_str = dia_conf.lower().replace('é', 'e').replace('á', 'a').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
        dia_semana_target = mapa_dias.get(dia_str, 4)
    else:
        dia_semana_target = int(dia_conf)
        
    min_dias_req = params.get('exacto_dias', params.get('min_dias', 1))
    
    k = sum(1 for lunes_f, dias_f in findes.items() if any(d_f not in emp.dias_licencia for d_f in dias_f))
    
    if params.get('dinamico_licencias', False):
        if dia_semana_target == 4:
            if k >= 3:
                target_dias = 1
            else:
                target_dias = 0
        else:
            target_dias = min_dias_req
    else:
        target_dias = min_dias_req

    is_exact_str = str(is_exact)
    print(f"  {emp.nombre:30s}: is_exact={is_exact_str:5s} | k={k} | target_dias={target_dias} | licencias={len(emp.dias_licencia)} days")
