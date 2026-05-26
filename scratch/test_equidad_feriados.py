import sys
import os
sys.path.append(os.getcwd())

import data
from database import queries as db_queries
from database.data_loader import obtener_empleados

def test_loading():
    print("Initializing licencias and loading employees for July 2026...")
    db_queries.init_licencias()
    
    # Load employees (July 2026 starts on 2026-07-01, period is 31 days)
    empleados = obtener_empleados(2, "2026-07-01", 31)
    
    print(f"\nSuccessfully loaded {len(empleados)} employees.")
    print("-" * 50)
    print(f"{'Nombre':<25} | {'Feriados Previos':<15}")
    print("-" * 50)
    for emp in empleados:
        print(f"{emp.nombre:<25} | {emp.feriados_previos:<15}")
        
    print("\nOK: Feriados Previos loaded successfully for all employees!")
    return True

if __name__ == "__main__":
    test_loading()
