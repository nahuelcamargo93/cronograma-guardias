import sqlite3
import sys
import os

sys.path.append(os.path.abspath('.'))
from database import queries as db_queries
from database.data_loader import obtener_empleados, obtener_turnos
import rule_engine as _re
import datetime

db_queries.init_licencias()
fecha_inicio = "2026-06-01"
fecha_fin = "2026-06-30"
fecha_inicio_dt = datetime.datetime.strptime(fecha_inicio, "%Y-%m-%d")
total_dias = 30

config_turnos, metadata_turnos_raw, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
    servicio_id=3, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
)
reglas_servicio_db = db_queries.cargar_reglas_servicio(3)
ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)
empleados = obtener_empleados(3, fecha_inicio, total_dias)

print("Active Employees list for Service 3:")
planta_count = 0
residente_count = 0
total_min_planta = 0
total_max_planta = 0

for emp in empleados:
    ref_date = fecha_inicio
    p_min = _re.resolver_parametros_regla('MIN_HORAS_MES_CALENDARIO', emp.nombre, ref_date, reglas_servicio_db, emp.reglas, ajustes_reglas)
    p_max = _re.resolver_parametros_regla('MAX_HORAS_MES_CALENDARIO', emp.nombre, ref_date, reglas_servicio_db, emp.reglas, ajustes_reglas)
    
    min_h = p_min.get('min_horas', 0) if (_re.regla_existe(p_min) and not _re.regla_suspendida(p_min)) else 0
    max_h = p_max.get('max_horas', 999) if (_re.regla_existe(p_max) and not _re.regla_suspendida(p_max)) else 999
    
    # Calculate licencias credit
    dias_lic = [d for d in range(total_dias) if d in emp.dias_licencia]
    p_cred = _re.resolver_parametros_regla('CREDITO_HORARIO_LICENCIA', emp.nombre, ref_date, reglas_servicio_db, emp.reglas, ajustes_reglas)
    if _re.regla_existe(p_cred):
        h_sem = p_cred.get('horas_por_semana', 36)
        horas_lic = int((h_sem / 7.0) * len(dias_lic) + 0.5)
    else:
        # fallback
        horas_lic = int((float(max_h) / total_dias) * len(dias_lic) + 0.5) if max_h != 999 else 0
        
    actual_max_workable = max_h - horas_lic if max_h != 999 else 999
    
    # Floor is min_h - horas_lic (or similar)
    if _re.regla_existe(p_min) and not _re.regla_suspendida(p_min):
        floor = int((min_h / total_dias) * total_dias + 0.5) # simple calculation
        floor_workable = max(0, floor - horas_lic)
    else:
        floor_workable = 0
        
    print(f"Name: {emp.nombre:35} | Rol: {emp.rol:10} | Licencias: {len(dias_lic)} days | Min: {min_h} (floor workable: {floor_workable}) | Max: {max_h} (max workable: {actual_max_workable})")
    
    if emp.rol == "Residente":
        residente_count += 1
    else:
        planta_count += 1
        total_min_planta += floor_workable
        total_max_planta += actual_max_workable

print(f"\nSummary:")
print(f"Planta count: {planta_count} | Total floor workable: {total_min_planta} | Total max workable: {total_max_planta}")
print(f"Residentes count: {residente_count}")
