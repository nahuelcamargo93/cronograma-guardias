"""
Inspección rápida: parámetros DESCANSO_ENTRE_TURNOS para servicio 3
y cuántas horas puede acumular un médico con las restricciones actuales.
"""
import sys, json, sqlite3
sys.path.insert(0, '.')

from data import FECHA_INICIO, FECHA_FIN, SERVICIO_ID, FERIADOS
from datetime import date, timedelta
from database import queries as db_queries, schema as db_schema
from database.data_loader import obtener_empleados, obtener_turnos
import rule_engine as _re

db_schema.inicializar_db()
db_queries.init_licencias()

fecha_inicio = FECHA_INICIO
fecha_fin = FECHA_FIN
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

reglas_servicio = db_queries.cargar_reglas_servicio(SERVICIO_ID)
ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)

empleados = obtener_empleados(SERVICIO_ID, fecha_inicio, dias_del_bloque)
turnos_dict = obtener_turnos(SERVICIO_ID)

print(f"=== TURNOS SERVICE 3 ===")
for nombre, t in turnos_dict.items():
    print(f"  {nombre}: hora_inicio={t.hora_inicio}, horas={t.horas}, puesto={t.puesto_nombre}")

print(f"\n=== EMPLEADOS ({len(empleados)}) ===")
planta = [e for e in empleados if 'Planta' in e.puestos_habilitados]
residentes = [e for e in empleados if 'Residente' in e.puestos_habilitados]
print(f"  Planta: {len(planta)}")
print(f"  Residentes: {len(residentes)}")

print(f"\n=== DESCANSO_ENTRE_TURNOS para primer empleado Planta ===")
if planta:
    emp = planta[0]
    params = _re.resolver_parametros_regla(
        'DESCANSO_ENTRE_TURNOS', emp.nombre, fecha_inicio,
        reglas_servicio, emp.reglas, ajustes_reglas
    )
    print(f"  {emp.nombre}: {params}")

print(f"\n=== MIN_HORAS_MES_CALENDARIO ===")
if planta:
    emp = planta[0]
    params = _re.resolver_parametros_regla(
        'MIN_HORAS_MES_CALENDARIO', emp.nombre, fecha_inicio,
        reglas_servicio, emp.reglas, ajustes_reglas
    )
    print(f"  Servicio: {params}")

print(f"\n=== EXACTO_FINDE_Y_DIA para primer Planta ===")
if planta:
    emp = planta[0]
    params = _re.resolver_parametros_regla(
        'EXACTO_FINDE_Y_DIA', emp.nombre, fecha_inicio,
        reglas_servicio, emp.reglas, ajustes_reglas
    )
    print(f"  {emp.nombre}: {params}")

print(f"\n=== ANALISIS: Horas máximas alcanzables vs MIN_HORAS ===")
print(f"Julio 2027 tiene {dias_del_bloque} días")

# Conteo de días
viernes = [(i, fecha_inicio_dt + timedelta(days=i)) for i in range(dias_del_bloque) if (fecha_inicio_dt + timedelta(days=i)).weekday() == 4]
sabdom = [(i, fecha_inicio_dt + timedelta(days=i)) for i in range(dias_del_bloque) if (fecha_inicio_dt + timedelta(days=i)).weekday() in (5,6)]
lunejue = [(i, fecha_inicio_dt + timedelta(days=i)) for i in range(dias_del_bloque) if (fecha_inicio_dt + timedelta(days=i)).weekday() in (0,1,2,3)]

print(f"  Viernes: {len(viernes)} días")
print(f"  Sáb+Dom: {len(sabdom)} días")
print(f"  Lun-Jue: {len(lunejue)} días")

# Con EXACTO_FINDE_Y_DIA HARD, k=5 fines de semana, k_dia=5 viernes:
# Target: 2 fines de semana (min 1 guardia de 24h sábado O domingo) + 2 viernes
# = 2*24 + 2*24 = 96h garantizadas
# Necesita 185h total -> 185-96 = 89h en Lun-Jue
# Con descanso post-24h: ¿cuántos días pierde?

print(f"\nEscenario con G_Planta (24h) en Viernes y Finde:")
print(f"  2 viernes × 24h = 48h")
print(f"  2 fines de semana × 24h = 48h")
print(f"  Total obligado = 96h")
print(f"  MIN_HORAS = 185h")
print(f"  Faltante en Lun-Jue = 89h")
print(f"  Lun-Jue disponibles = {len(lunejue)} días = máx {len(lunejue)*24}h con guardias 24h")
print(f"  O máx {len(lunejue)*12}h con turnos de 12h")
print(f"  MAX_HORAS = 198h")

# El problema: si usa 2 viernes + 2 fines (4 guardias 24h = 96h)
# Para llegar a 185h necesita 89h más en 17 días Lun-Jue
# Con 12h por día: 89/12 = 7.4 → 8 días de 12h = 96h ✓
# Pero: ¿el descanso post-24h (G_Planta) no ocupa el día siguiente?

# Si G_Planta (viernes 24h) requiere 24h descanso,
# el sábado queda bloqueado (pero sería finde y el médico ya puede tener guardia ahí)
# Si G_Planta (sábado 24h) requiere 24h descanso, el domingo queda bloqueado
# → Esto podría hacer que no pueda trabajar el domingo si ya trabajó el sábado

# Veamos: si trabaja viernes 24h (08:00-08:00 sábado), necesita 24h descanso = libre hasta sábado 08:00
# = puede trabajar sábado 08:00 ✓ (si descanso es exacto 24h)
print(f"\nDescanso post-G_Planta (24h):")
print(f"  Si descanso=48h: Viernes 08:00 + 24h + 48h = Domingo 08:00 libre")
print(f"  Si descanso=24h: Viernes 08:00 + 24h + 24h = Sábado 08:00 libre (puede trabajar Sáb)")
