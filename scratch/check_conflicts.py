import sys
import os
sys.path.append(r"c:\Users\asus\Desktop\Ryoko\cronograma_inteligente")
from database import queries as q
from datetime import date, timedelta

q.init_licencias()
emps = q.obtener_personal_db(3)
regras = q.cargar_reglas_personal(3)
start = date.fromisoformat('2026-06-01')

mapa_dias = {'Lunes':0,'Martes':1,'Miercoles':2,'Jueves':3,'Viernes':4,'Sabado':5,'Domingo':6}

for e in emps:
    name = e['Nombre']
    lic = q.LAR.get(name, []) + q.LPP.get(name, [])
    asigs = regras.get(name, {}).get('ASIGNACION_FIJA', [])
    for r in asigs:
        dia_sem = mapa_dias.get(r.get('Dia'))
        if dia_sem is None: continue
        for d in range(30):
            curr_date = start + timedelta(days=d)
            if curr_date.weekday() == dia_sem:
                curr_date_str = curr_date.isoformat()
                for (ls, le) in lic:
                    if ls <= curr_date_str <= le:
                        print(f"CONFLICT: {name} has ASIGNACION_FIJA on {curr_date_str} but is on LICENCIA")
