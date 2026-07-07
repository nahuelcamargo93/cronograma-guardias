import sys
import os
import datetime
from datetime import date, timedelta

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from database import queries as db_queries
from database import schema as db_schema
from database.data_loader import obtener_empleados
from restricciones.hard._utils import get_semanas_calendario

def main():
    servicio_id = 2
    fecha_inicio = "2026-08-01"
    fecha_fin = "2026-09-06"
    
    db_schema.inicializar_db()
    db_queries.init_licencias(servicio_id)
    
    fecha_inicio_dt = date.fromisoformat(fecha_inicio)
    fecha_fin_dt = date.fromisoformat(fecha_fin)
    total_dias = (fecha_fin_dt - fecha_inicio_dt).days + 1
    
    empleados = obtener_empleados(servicio_id, fecha_inicio, total_dias)
    semanas = get_semanas_calendario(total_dias, fecha_inicio_dt)
    
    for emp in empleados:
        if emp.nombre == 'ORTIZ LAURA':
            print(f"Empleado: {emp.nombre}")
            print(f"Dias licencia: {emp.dias_licencia}")
            for (iso_y, iso_w), days in semanas.items():
                licencias_en_bloque = sum(1 for d, _ in days if d in emp.dias_licencia)
                print(f"Semana {iso_y}-W{iso_w}:")
                print(f"  days: {days}")
                print(f"  len(days): {len(days)}")
                print(f"  licencias_en_bloque: {licencias_en_bloque}")
                print(f"  licencias_en_bloque == len(days): {licencias_en_bloque == len(days)}")

if __name__ == "__main__":
    main()
