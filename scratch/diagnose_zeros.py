import sys
import os
sys.path.append(os.getcwd())

import data
from database import queries as db_queries
from database.data_loader import obtener_empleados

db_queries.init_licencias()
empleados = obtener_empleados(data.SERVICIO_ID, data.FECHA_INICIO, 31)

print(f"Total empleados: {len(empleados)}")
for emp in empleados:
    # July 2026 is 31 days
    # Let's compute f_hab_mes for this employee
    # A weekend is "habiles" if not blocked on Saturday and Sunday
    # Let's count weekend days in July 2026:
    # 2026-07-01 (offset_dia = 2, Wednesday)
    # Weekends (Saturday=5, Sunday=6) relative to July 1st:
    # Sat July 4th (day 3), Sun July 5th (day 4)
    # Sat July 11th (day 10), Sun July 12th (day 11)
    # Sat July 18th (day 17), Sun July 19th (day 18)
    # Sat July 25th (day 24), Sun July 26th (day 25)
    
    offset_dia = 2
    dias_licencia = emp.dias_licencia
    
    findes_habiles_actual = 0
    # Let's check each of the 4 weekends
    weekends = [(3, 4), (10, 11), (17, 18), (24, 25)]
    for s, dom in weekends:
        if s not in dias_licencia and dom not in dias_licencia:
            findes_habiles_actual += 1
            
    f_trab_prev = emp.findes_semanas_previos
    f_hab_prev = emp.findes_habiles_previos
    
    f_hab_total = f_hab_prev + findes_habiles_actual
    
    print(f"Nombre: {emp.nombre:25} | Prev Hab: {f_hab_prev:2} | Actual Hab: {findes_habiles_actual:2} | Total Hab: {f_hab_total:2}")
    if f_hab_total == 0:
        print("   WARNING: f_hab_total is 0!")
