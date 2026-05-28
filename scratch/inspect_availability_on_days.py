import sqlite3
import datetime
from datetime import timedelta, datetime
import sys
import os

sys.path.append(os.path.abspath('.'))
from database import queries as db_queries
from database.data_loader import obtener_empleados
import rule_engine as _re

db_queries.init_licencias()
fecha_inicio = "2026-06-01"
fecha_fin = "2026-06-30"
total_dias = 30
fecha_inicio_dt = datetime.strptime(fecha_inicio, "%Y-%m-%d")

reglas_servicio_db = db_queries.cargar_reglas_servicio(3)
ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)
empleados = obtener_empleados(3, fecha_inicio, total_dias)

target_days = [3, 6, 10, 13, 16, 21, 24] # 0-indexed days corresponding to June 4, 7, 11, 14, 17, 22, 25

print("Availability on Quintero's assigned days:")
for d in target_days:
    fecha_str = (fecha_inicio_dt + timedelta(days=d)).strftime("%Y-%m-%d")
    print(f"\n========================================\nDay {d+1}: {fecha_str} ({ (fecha_inicio_dt + timedelta(days=d)).strftime('%A') })")
    
    available_planta = []
    unavailable_planta = []
    
    for emp in empleados:
        if emp.rol == "Residente":
            continue
        # Check license
        if d in emp.dias_licencia:
            unavailable_planta.append(f"{emp.nombre} (License)")
            continue
        # Check franco forzado
        p_franco = _re.resolver_parametros_regla('FRANCO_FORZADO', emp.nombre, fecha_str, reglas_servicio_db, emp.reglas, ajustes_reglas)
        if _re.regla_existe(p_franco) and not _re.regla_suspendida(p_franco):
            unavailable_planta.append(f"{emp.nombre} (Franco Forzado)")
            continue
            
        available_planta.append(emp.nombre)
        
    print(f"Available Planta doctors ({len(available_planta)}): {available_planta}")
    print(f"Unavailable ({len(unavailable_planta)}): {unavailable_planta}")
