import sys
import os
import datetime

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from database import queries as db_queries
from database import schema as db_schema
from database.data_loader import obtener_empleados

def main():
    servicio_id = 2
    fecha_inicio = "2026-08-01"
    dias_del_bloque = 37 # 1/8 al 6/9

    db_schema.inicializar_db()
    db_queries.init_licencias(servicio_id)

    empleados = obtener_empleados(servicio_id, fecha_inicio, dias_del_bloque)
    
    for emp in empleados:
        if emp.nombre in ('ORTIZ LAURA', 'VELEZ DANIEL'):
            print(f"Empleado: {emp.nombre}")
            print(f"  dias_licencia: {sorted(list(emp.dias_licencia))}")
            
if __name__ == "__main__":
    main()
