import sys
import os
sys.path.append(os.getcwd())

import data
from database import queries as db_queries
from database.data_loader import obtener_empleados

db_queries.init_licencias()
empleados = obtener_empleados(data.SERVICIO_ID, data.FECHA_INICIO, 31)

for emp in empleados:
    print(f"Nombre: {emp.nombre}")
    print(f"  Rol: {emp.rol}")
    print(f"  Puestos habilitados: {emp.puestos_habilitados}")
    print(f"  Reglas: {emp.reglas.keys() if hasattr(emp, 'reglas') and emp.reglas else None}")
    print(f"  Dias licencia: {emp.dias_licencia}")
