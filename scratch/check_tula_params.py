import sys
import os
import datetime
from datetime import date

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from database import queries as db_queries
from database import schema as db_schema
from database.data_loader import obtener_empleados
import rule_engine as _re

def main():
    servicio_id = 2
    fecha_inicio = "2026-08-01"
    
    db_schema.inicializar_db()
    db_queries.init_licencias(servicio_id)
    
    empleados = obtener_empleados(servicio_id, fecha_inicio, 31)
    reglas_servicio_db = db_queries.cargar_reglas_servicio(servicio_id)
    ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, "2026-08-31")
    
    ajustes_servicio = db_queries.cargar_ajustes_reglas_servicio(fecha_inicio, "2026-08-31", servicio_id)
    ajustes_reglas['__servicio__'] = ajustes_servicio
    
    for emp in empleados:
        if emp.nombre == 'TULA DAIANA':
            fecha_lunes = "2026-07-27"
            params = _re.resolver_parametros_regla(
                'MIN_FRANCOS_SEMANA', emp.nombre, fecha_lunes,
                reglas_servicio_db, emp.reglas, ajustes_reglas
            )
            print(f"Empleado: {emp.nombre}")
            print(f"  params: {params}")
            print(f"  tipo: {type(params)}")
            if isinstance(params, dict):
                print(f"  modo: {params.get('modo')}")

if __name__ == "__main__":
    main()
