import sys
import os
from datetime import date, timedelta

sys.path.append(os.getcwd())

import data
from database import queries as db_queries
from database.data_loader import obtener_empleados

db_queries.init_licencias()
empleados = obtener_empleados(data.SERVICIO_ID, data.FECHA_INICIO, 31)

fecha_inicio_dt = date.fromisoformat(data.FECHA_INICIO)
offset_dia = 2 # July 1st 2026 is Wednesday
dias_del_bloque = 31

# Calculate findes_habiles_actual for July 2026
# Let's group days by Monday-Sunday week
dias_por_semana_calendario = {}
for d in range(dias_del_bloque):
    fecha_d = fecha_inicio_dt + timedelta(days=d)
    lunes_semana = fecha_d - timedelta(days=fecha_d.weekday())
    sem_key = lunes_semana.isoformat()
    dias_por_semana_calendario.setdefault(sem_key, []).append(d)

print(f"Checking {len(empleados)} employees for SERVICIO_ID = {data.SERVICIO_ID}")
zero_hab_total = []

for emp in empleados:
    nombre = emp.nombre
    dias_bloqueados_persona = emp.dias_licencia
    f_hab_prev = emp.findes_habiles_previos
    f_trab_prev = emp.findes_semanas_previos
    
    # Calculate findes_habiles_actual
    findes_habiles_actual = 0
    for sem_key, dias_semana_actual in dias_por_semana_calendario.items():
        sabados = [d for d in dias_semana_actual if ((d + offset_dia) % 7) == 5]
        domingos = [d for d in dias_semana_actual if ((d + offset_dia) % 7) == 6]
        if sabados and domingos:
            s = sabados[0]
            dom = domingos[0]
            if s not in dias_bloqueados_persona and dom not in dias_bloqueados_persona:
                findes_habiles_actual += 1
                
    f_hab_total = f_hab_prev + findes_habiles_actual
    print(f"Emp: {nombre:25s} | f_hab_prev: {f_hab_prev} | f_hab_actual: {findes_habiles_actual} | f_hab_total: {f_hab_total}")
    if f_hab_total == 0:
        zero_hab_total.append(nombre)

print(f"\nEmployees with f_hab_total == 0: {zero_hab_total}")
