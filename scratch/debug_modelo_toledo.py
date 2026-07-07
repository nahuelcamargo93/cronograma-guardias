import sys, os
sys.path.append(os.getcwd())

import sqlite3
import pandas as pd
from datetime import date, timedelta
import rule_engine as _re
import database.queries as q
from database.data_loader import obtener_empleados, obtener_turnos

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
config_oferta, _, _, _ = q.cargar_configuracion_turnos(servicio_id)
demanda_turnos = config_oferta
fecha_inicio_dt = date.fromisoformat(fecha_inicio)
offset_dia = fecha_inicio_dt.weekday()
feriados = set()

mapa_dias = {
    "Lunes": 0, "Martes": 1, "Miercoles": 2, "Jueves": 3,
    "Viernes": 4, "Sabado": 5, "Domingo": 6
}

emp = next(e for e in empleados if e.nombre == 'Toledo, Andrea')

print(f"=== ANALYZING ALL DAYS FOR {emp.nombre} ===")
for dia in range(dias_del_bloque):
    dia_semana = (dia + offset_dia) % 7
    fecha_dia_str = (fecha_inicio_dt + timedelta(days=dia)).isoformat()
    
    params = _re.resolver_parametros_regla(
        'ASIGNACION_FIJA', emp.nombre, fecha_dia_str,
        reglas_servicio, emp.reglas, ajustes_reglas_personal or {}
    )
    
    if _re.regla_existe(params) and isinstance(params, list):
        params_franco = _re.resolver_parametros_regla(
            'FRANCO_FORZADO', emp.nombre, fecha_dia_str,
            reglas_servicio, emp.reglas, ajustes_reglas_personal or {}
        )
        tiene_franco = _re.regla_existe(params_franco) and not _re.regla_suspendida(params_franco)
        
        matches = []
        for asig in params:
            fecha_asig = asig.get('Fecha')
            dia_asig   = asig.get('Dia')
            
            es_por_fecha = bool(fecha_asig and fecha_asig == fecha_dia_str)
            es_por_dia = bool(dia_asig and mapa_dias.get(dia_asig) == dia_semana and dia not in feriados)
            
            match = False
            if es_por_fecha:
                match = True
            elif es_por_dia:
                if not tiene_franco:
                    match = True
            if match:
                matches.append(asig)
        
        print(f"Day {dia} ({fecha_dia_str}, wd={dia_semana}): ASIGS found: {params} | tiene_franco={tiene_franco} | Matches: {matches}")
