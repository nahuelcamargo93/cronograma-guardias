import os
import sys

# Asegurar que la raíz del proyecto está en el path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import datetime
from database import queries as db_queries
from database.data_loader import obtener_empleados, obtener_turnos

def check_demand():
    servicio_id = 3
    fecha_inicio = "2026-07-01"
    fecha_fin = "2026-07-31"
    
    fecha_inicio_dt = datetime.datetime.strptime(fecha_inicio, "%Y-%m-%d")
    fecha_fin_dt    = datetime.datetime.strptime(fecha_fin,    "%Y-%m-%d")
    total_dias = (fecha_fin_dt - fecha_inicio_dt).days + 1
    
    # Cargar datos
    config_turnos, metadata_turnos_raw, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
        servicio_id=servicio_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
    )
    empleados = obtener_empleados(servicio_id, fecha_inicio, total_dias)
    turnos_dict = obtener_turnos(servicio_id)
    
    feriados_indices = []
    feriados_db = db_queries.obtener_feriados(fecha_inicio, fecha_fin, servicio_id=servicio_id)
    for f_str in feriados_db:
        f_dt = datetime.datetime.strptime(f_str, "%Y-%m-%d")
        delta = (f_dt - fecha_inicio_dt).days
        if 0 <= delta < total_dias:
            feriados_indices.append(delta)
            
    offset_dia = fecha_inicio_dt.weekday()
    
    # Calcular días Semana vs Finde
    cant_semana = 0
    cant_finde = 0
    for d in range(total_dias):
        es_f = ((d + offset_dia) % 7) >= 5 or d in feriados_indices
        if es_f:
            cant_finde += 1
        else:
            cant_semana += 1
            
    print(f"Total días: {total_dias} (Semana: {cant_semana}, Finde/Feriados: {cant_finde})")
    print(f"Cantidad de empleados: {len(empleados)}")
    
    # Calcular horas de demanda totales
    # Para cada día se requiere una cobertura. Vamos a calcularla por día
    horas_demanda_total = 0
    
    # Mapear turnos a puestos y horas
    # Para saber qué turnos cubren qué puestos, o directamente ver la demanda
    # En cobertura_dinamica.py, la demanda se define en demanda_req (por ventana horaria, cantidad_min/max por puesto)
    # Veamos qué puestos hay y cuáles son las demandas por ventana
    print("\n--- Demanda por tipo de día (Semana) ---")
    demanda_semana_horas = 0
    for d_req in demanda_req.get("Semana", []):
        h_start = d_req["hora_inicio"]
        h_end = d_req["hora_fin"]
        # Calcular duración de la ventana
        # Como estimación, asumamos que las ventanas de Planta y Residente son de 24h o 12h
        # Vamos a ver los detalles de demanda_req
        c_min = d_req.get("cantidad_min", 0) or 0
        print(f"Puesto: {d_req['puesto']} | Ventana: {h_start} - {h_end} | Cant Min: {c_min}")
        
    print("\n--- Demanda por tipo de día (Finde_Feriado) ---")
    for d_req in demanda_req.get("Finde_Feriado", []):
        h_start = d_req["hora_inicio"]
        h_end = d_req["hora_fin"]
        c_min = d_req.get("cantidad_min", 0) or 0
        print(f"Puesto: {d_req['puesto']} | Ventana: {h_start} - {h_end} | Cant Min: {c_min}")
        
    # Mapear turnos configurados y sus horas
    print("\n--- Turnos configurados ---")
    for t_name, t_info in turnos_dict.items():
        print(f"Turno: {t_name} | Horas: {t_info.horas} | Puesto: {t_info.puesto_nombre}")

if __name__ == "__main__":
    check_demand()
