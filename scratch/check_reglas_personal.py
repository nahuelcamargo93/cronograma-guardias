import sys
import os
sys.path.append(os.getcwd())

import data
from database import queries as db_queries

reglas_personal = db_queries.cargar_reglas_personal(data.SERVICIO_ID)
for nombre, reglas in reglas_personal.items():
    print(f"Empleado: {nombre}")
    for r_name, r_val in reglas.items():
        print(f"  Regla: {r_name} | Valor: {r_val}")
