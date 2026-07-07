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
from restricciones.hard._utils import get_semanas_calendario

def main():
    servicio_id = 2
    fecha_inicio = "2026-08-01"
    fecha_fin = "2026-08-31"
    
    db_schema.inicializar_db()
    db_queries.init_licencias(servicio_id)
    
    fecha_inicio_dt = date.fromisoformat(fecha_inicio)
    fecha_fin_dt = date.fromisoformat(fecha_fin)
    total_dias = (fecha_fin_dt - fecha_inicio_dt).days + 1
    
    empleados = obtener_empleados(servicio_id, fecha_inicio, total_dias)
    reglas_servicio_db = db_queries.cargar_reglas_servicio(servicio_id)
    ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)
    
    ajustes_servicio = db_queries.cargar_ajustes_reglas_servicio(fecha_inicio, fecha_fin, servicio_id)
    ajustes_reglas['__servicio__'] = ajustes_servicio
    
    semanas = get_semanas_calendario(total_dias, fecha_inicio_dt)
    
    for emp in empleados:
        if emp.nombre == 'TULA DAIANA':
            for (iso_y, iso_w), days in semanas.items():
                fl = days[0][1]
                fecha_lunes = (fl - datetime.timedelta(days=fl.isocalendar()[2] - 1)).isoformat()
                params = _re.resolver_parametros_regla(
                    'MIN_FRANCOS_SEMANA', emp.nombre, fecha_lunes,
                    reglas_servicio_db, emp.reglas, ajustes_reglas
                )
                print(f"Semana {iso_y}-W{iso_w} (fecha_lunes={fecha_lunes}):")
                print(f"  params: {params}")
                if isinstance(params, dict):
                    modo = params.get('modo', 'HARD').upper()
                    print(f"  modo resolved: {modo}")

if __name__ == "__main__":
    main()
