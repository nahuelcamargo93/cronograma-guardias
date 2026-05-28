"""
Diagnóstico específico: ¿cuál restricción causa la imposibilidad con EXACTO_FINDE_Y_DIA HARD?
Ejecutar contra el modelo real, activando/desactivando reglas para aislar el conflicto.
"""
import sys
sys.path.insert(0, '.')

from data import FECHA_INICIO, FECHA_FIN, SERVICIO_ID, FERIADOS
from datetime import date, timedelta
from db import (
    obtener_empleados, obtener_turnos, obtener_demanda_turnos,
    obtener_reglas_servicio, obtener_ajustes_reglas_personal,
    obtener_historial_semana_previa, obtener_ajustes_demanda,
    obtener_demanda_requerida
)
from hard_rules import (
    _aplicar_licencias, _aplicar_descanso_entre_turnos,
    _aplicar_un_solo_turno_por_dia, _aplicar_min_horas_mes_calendario,
    _aplicar_max_horas_mes_calendario, _aplicar_exacto_finde_y_dia,
    _is_finde, time_to_float
)
from ortools.sat.python import cp_model

fecha_inicio_dt = date.fromisoformat(FECHA_INICIO)
fecha_fin_dt = date.fromisoformat(FECHA_FIN)
dias_del_bloque = (fecha_fin_dt - fecha_inicio_dt).days + 1
offset_dia = fecha_inicio_dt.weekday()

feriados_iso = set(FERIADOS)
feriados = [
    (date.fromisoformat(f) - fecha_inicio_dt).days
    for f in feriados_iso
    if fecha_inicio_dt <= date.fromisoformat(f) <= fecha_fin_dt
]

empleados = obtener_empleados(SERVICIO_ID)
turnos_dict = obtener_turnos(SERVICIO_ID)
demanda_turnos = obtener_demanda_turnos(SERVICIO_ID)
reglas_servicio = obtener_reglas_servicio(SERVICIO_ID)
ajustes_reglas = obtener_ajustes_reglas_personal(SERVICIO_ID)
historial = obtener_historial_semana_previa(SERVICIO_ID, FECHA_INICIO)
ajustes_demanda = obtener_ajustes_demanda(SERVICIO_ID, FECHA_INICIO, FECHA_FIN)
demanda_req = obtener_demanda_requerida(SERVICIO_ID, FECHA_INICIO, FECHA_FIN)

print(f"Empleados: {len(empleados)}")
print(f"Período: {FECHA_INICIO} a {FECHA_FIN} ({dias_del_bloque} días)")
print(f"Offset día: {offset_dia} (0=Lun, 4=Vie)")

# Analizar los parámetros de descanso para el servicio 3
import rule_engine as _re
for emp in empleados[:3]:
    params_desc = _re.resolver_parametros_regla(
        'DESCANSO_ENTRE_TURNOS', emp.nombre, FECHA_INICIO,
        reglas_servicio, emp.reglas, ajustes_reglas
    )
    print(f"\nDESCANSO para {emp.nombre}: {params_desc}")

print("\n=== ANALIZANDO DESCANSO POST-GUARDIA 24H ===")
for emp in empleados[:1]:
    params_desc = _re.resolver_parametros_regla(
        'DESCANSO_ENTRE_TURNOS', emp.nombre, FECHA_INICIO,
        reglas_servicio, emp.reglas, ajustes_reglas
    )
    if params_desc and isinstance(params_desc, dict):
        por_turno = params_desc.get('por_turno', {})
        print(f"  Config por turno: {por_turno}")
        # ¿Cuál turno aplica a G_Planta (24h)?
        for k, v in por_turno.items():
            if 'G' in k or '24' in k:
                print(f"  -> Guardia de 24h: descanso={v}h")

print("\n=== VERIFICANDO PARÁMETROS DE EXACTO_FINDE_Y_DIA ===")
import json, sqlite3
con = sqlite3.connect('cronograma_inteligente.db')
cur = con.cursor()
cur.execute("SELECT parametros_json FROM servicios_reglas WHERE servicio_id=3 AND codigo_regla='EXACTO_FINDE_Y_DIA'")
row = cur.fetchone()
params_efyd = json.loads(row[0])
print(f"Parámetros: {json.dumps(params_efyd, indent=2, ensure_ascii=False)}")
con.close()

# Contar viernes en julio 2027
viernes_count = sum(1 for i in range(dias_del_bloque) if (fecha_inicio_dt + timedelta(days=i)).weekday() == 4)
finde_groups = {}
for i in range(dias_del_bloque):
    d = fecha_inicio_dt + timedelta(days=i)
    if _is_finde(i, offset_dia, feriados):
        lunes = (d - timedelta(days=d.weekday())).isoformat()
        finde_groups.setdefault(lunes, []).append(i)

print(f"\nViernes en el mes: {viernes_count}")
print(f"Grupos de finde: {len(finde_groups)}")

mapping_f = params_efyd.get('findes_por_disponibilidad', {})
mapping_d = params_efyd.get('dias_por_disponibilidad', {})

target_f = mapping_f.get(str(len(finde_groups)), 0)
target_d = mapping_d.get(str(viernes_count), 0)
print(f"Target finde (k={len(finde_groups)}): {target_f} fines de semana = {target_f * 24}h")
print(f"Target viernes (k_dia={viernes_count}): {target_d} viernes = {target_d * 24}h")
print(f"Total horas garantizadas EXACTO: {(target_f + target_d) * 24}h")

min_horas = 185
max_horas = 198
print(f"MIN_HORAS exigidas: {min_horas}h")
print(f"MAX_HORAS permitidas: {max_horas}h")
print(f"Horas adicionales a conseguir: {min_horas - (target_f + target_d) * 24}h")
print(f"¿La suma finde+viernes ya supera MAX?: {(target_f + target_d) * 24 > max_horas}")
