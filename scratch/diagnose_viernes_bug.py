"""
Diagnóstico específico del bug de EXACTO_DIA_ESPECIFICO_MES:
- Por qué Matricardi tiene 2 viernes en vez de 1
- Cómo funciona exactamente el cálculo de `k` y `dinamico_licencias`
"""
import sys, os
sys.path.append(os.path.abspath('.'))
from database import queries as db_queries
from database.data_loader import obtener_empleados
import rule_engine as _re
from datetime import date, timedelta

FECHA_INICIO = "2026-06-01"
FECHA_FIN = "2026-06-30"
SERVICIO_ID = 3

db_queries.init_licencias()
reglas_servicio = db_queries.cargar_reglas_servicio(SERVICIO_ID)
ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(FECHA_INICIO, FECHA_FIN)
empleados = obtener_empleados(SERVICIO_ID, FECHA_INICIO, 30)

fecha_ini = date.fromisoformat(FECHA_INICIO)

# Simular el cálculo de k y target_dias de soft_rules.py líneas 940-1000
offset_dia = fecha_ini.weekday()  # 6 = Domingo (junio 2026 empieza el lunes)

# Identificar fines de semana y feriados
FERIADOS = []
feriados_indices = []

# Calcular findes igual que soft_rules.py
dias_del_bloque = 30
finds = {}
for d_f in range(dias_del_bloque):
    fecha_df = fecha_ini + timedelta(days=d_f)
    dia_semana_f = (d_f + offset_dia) % 7
    es_finde_f = (dia_semana_f >= 5) or (d_f in feriados_indices)
    if es_finde_f:
        lunes_f = (fecha_df - timedelta(days=fecha_df.weekday())).isoformat()
        finds.setdefault(lunes_f, []).append(d_f)

print(f"=== ANÁLISIS EXACTO_DIA_ESPECIFICO_MES para Jun 2026 ===")
print(f"offset_dia (weekday de inicio): {offset_dia} (0=Lun...6=Dom)")
print(f"\nFines de semana detectados:")
for lunes, dias in sorted(finds.items()):
    fechas = [(fecha_ini + timedelta(days=d)).isoformat() for d in dias]
    print(f"  Semana del {lunes}: dias={fechas}")

print()

# Calcular viernes del mes
mapa_dias = {"lunes": 0, "martes": 1, "miercoles": 2, "jueves": 3, "viernes": 4, "sabado": 5, "domingo": 6}
dia_semana_target = 4  # Viernes

viernes_del_mes = []
for d in range(dias_del_bloque):
    fecha_d = fecha_ini + timedelta(days=d)
    if fecha_d.weekday() == dia_semana_target:
        viernes_del_mes.append((d, fecha_d.isoformat()))

print(f"Viernes del mes: {[v[1] for v in viernes_del_mes]}")
print(f"Total viernes: {len(viernes_del_mes)}")

print()
print("=== POR PERSONA ===")
for emp in empleados:
    if 'atricard' not in emp.nombre.lower() and 'acheco' not in emp.nombre.lower():
        continue
    
    params_exacto = _re.resolver_parametros_regla(
        'EXACTO_DIA_ESPECIFICO_MES', emp.nombre, FECHA_INICIO,
        reglas_servicio, emp.reglas, ajustes_reglas
    )
    params_min = _re.resolver_parametros_regla(
        'MIN_DIA_ESPECIFICO_MES', emp.nombre, FECHA_INICIO,
        reglas_servicio, emp.reglas, ajustes_reglas
    )
    
    has_exacto = _re.regla_existe(params_exacto) and not _re.regla_suspendida(params_exacto)
    has_min = _re.regla_existe(params_min) and not _re.regla_suspendida(params_min)
    
    if has_exacto and params_min is not None and _re.regla_suspendida(params_min):
        has_exacto = False
    
    # Calcular k: semanas en que el empleado puede trabajar (no tiene licencia el finde)
    k = sum(1 for lunes_f, dias_f in finds.items() if any(d_f not in emp.dias_licencia for d_f in dias_f))
    
    # Calcular viernes disponibles (no en licencia, no en franco)
    viernes_disponibles = []
    for d, fecha_str in viernes_del_mes:
        if d in emp.dias_licencia:
            continue
        p_franco = _re.resolver_parametros_regla('FRANCO_FORZADO', emp.nombre, fecha_str, reglas_servicio, emp.reglas, ajustes_reglas)
        if _re.regla_existe(p_franco) and not _re.regla_suspendida(p_franco):
            continue
        viernes_disponibles.append(fecha_str)
    
    # Calcular target_dias
    if params_exacto and params_exacto.get('dinamico_licencias', False):
        if k >= 3:
            target_dias = 1
        else:
            target_dias = 0
    elif params_min and params_min.get('dinamico_licencias', False):
        if k >= 3:
            target_dias = 1
        else:
            target_dias = 0
    else:
        target_dias = 1
    
    print(f"\n--- {emp.nombre} ---")
    print(f"  dias_licencia: {sorted(emp.dias_licencia)}")
    print(f"  k (semanas finde disponibles): {k}")
    print(f"  viernes disponibles: {viernes_disponibles}")
    print(f"  target_dias calculado: {target_dias}")
    print(f"  has_exacto: {has_exacto}, has_min: {has_min}")
    print(f"  params_exacto: {params_exacto}")
    print(f"  NOTA: k cuenta FINES DE SEMANA, NO VIERNES. Hay {len(viernes_del_mes)} viernes en junio 2026.")
    print(f"  BUG?: k deberia contar viernes disponibles, no semanas con finde disponible")
