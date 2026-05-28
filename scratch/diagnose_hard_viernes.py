"""
Diagnóstico rápido: con EXACTO_DIA_ESPECIFICO_MES_HARD activa, 
¿cuántos viernes disponibles tiene cada persona del servicio 3?
Si alguien necesita 1 viernes pero solo tiene 1 disponible, 
puede chocar con DESCANSO_ENTRE_TURNOS si trabajó el jueves.
"""
import sys, os
sys.path.append(os.path.abspath('.'))
from database import queries as db_queries
from database.data_loader import obtener_empleados
import rule_engine as _re
from datetime import date, timedelta

FECHA_INICIO = '2026-06-01'
SERVICIO_ID = 3
db_queries.init_licencias()
reglas_servicio = db_queries.cargar_reglas_servicio(SERVICIO_ID)
ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(FECHA_INICIO, '2026-06-30')
empleados = obtener_empleados(SERVICIO_ID, FECHA_INICIO, 30)
fecha_ini = date.fromisoformat(FECHA_INICIO)
offset_dia = fecha_ini.weekday()
dias_del_bloque = 30

# Viernes del mes
viernes_del_mes = [(d, (fecha_ini + timedelta(days=d)).isoformat()) 
                   for d in range(dias_del_bloque) 
                   if (fecha_ini + timedelta(days=d)).weekday() == 4]

print(f"Viernes de junio 2026: {[v[1] for v in viernes_del_mes]}")
print()
print(f"{'Nombre':<45} {'V.Disp':>7} {'Has_Hard':>9} {'Suspendida':>11}")
print("-"*75)

for emp in empleados:
    # Verificar si tiene la regla hard activa
    params_hard = _re.resolver_parametros_regla(
        'EXACTO_DIA_ESPECIFICO_MES_HARD', emp.nombre, FECHA_INICIO,
        reglas_servicio, emp.reglas, ajustes_reglas
    )
    has_hard = _re.regla_existe(params_hard) and not _re.regla_suspendida(params_hard)
    is_suspended = _re.regla_existe(params_hard) and _re.regla_suspendida(params_hard)
    
    # Contar viernes disponibles (sin licencia, sin franco)
    viernes_disponibles = []
    for d, fecha_str in viernes_del_mes:
        if d in emp.dias_licencia:
            continue
        p_franco = _re.resolver_parametros_regla('FRANCO_FORZADO', emp.nombre, fecha_str, reglas_servicio, emp.reglas, ajustes_reglas)
        if _re.regla_existe(p_franco) and not _re.regla_suspendida(p_franco):
            continue
        viernes_disponibles.append(fecha_str)
    
    flag = ""
    if has_hard and len(viernes_disponibles) == 0:
        flag = "  *** CONFLICTO: 0 viernes pero hard=1 ***"
    
    print(f"{emp.nombre:<45} {len(viernes_disponibles):>7} {str(has_hard):>9} {str(is_suspended):>11}{flag}")
