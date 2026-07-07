import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
from database import queries as q
from database.data_loader import obtener_empleados

q.init_licencias(4)
empleados = obtener_empleados(4, '2026-07-01', 31)

for e in empleados:
    if e.nombre in ['FERNANDEZ Claudia Elizabeth', 'QUINTANA Felipe Gabriel', 'SUÑER Mara Tatiana', 'BRIZUELA Irma']:
        print(f"\n--- {e.nombre} ---")
        print(f"Categoria: {e.categoria}")
        print(f"Puestos habilitados: {e.puestos_habilitados}")
        print(f"Reglas: {e.reglas}")
        
        # Now simulate com.py check for each category code
        for cat_code in ['A', 'B', 'C', 'D']:
            # Simulate com.py logic
            puestos_hab = list(e.puestos_habilitados)
            reglas = e.reglas
            excluir_turnos = []
            if isinstance(reglas, dict) and 'EXCLUIR_TURNOS' in reglas:
                excluir_rules = reglas['EXCLUIR_TURNOS']
                if isinstance(excluir_rules, list) and len(excluir_rules) > 0:
                    excluir_turnos = excluir_rules[0].get('turnos', [])
            
            cat_shifts = {
                'A': ["00-06_Monitorista", "00-06_Supervisor", "00-06_Administrativo"],
                'B': ["06-12_Monitorista", "06-12_Supervisor", "06-12_Administrativo"],
                'C': ["12-18_Monitorista", "12-18_Supervisor", "12-18_Administrativo"],
                'D': ["18-24_Monitorista", "18-24_Supervisor", "18-24_Administrativo"]
            }.get(cat_code, [])
            
            elegible = False
            for shift in cat_shifts:
                puesto_shift = shift.split('_')[1]
                if puesto_shift in puestos_hab and shift not in excluir_turnos:
                    elegible = True
                    break
            
            is_in_cat = (e.categoria == cat_code) or elegible
            print(f"Category {cat_code}: is_in_cat={is_in_cat} (db_cat={e.categoria == cat_code}, elegible={elegible}, excluir_turnos={excluir_turnos})")
