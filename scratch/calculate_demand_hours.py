import sys
sys.path.insert(0, 'c:/Users/asus/Desktop/Ryoko/cronograma_inteligente')

import pandas as pd
import datetime
from datetime import date, timedelta
from data import FECHA_INICIO, FECHA_FIN, FERIADOS, SERVICIO_ID
from database import queries as db_queries
from database.data_loader import obtener_empleados, obtener_turnos

def check_capacity():
    fecha_inicio_dt = datetime.datetime.strptime(FECHA_INICIO, "%Y-%m-%d")
    fecha_fin_dt    = datetime.datetime.strptime(FECHA_FIN,    "%Y-%m-%d")
    total_dias = (fecha_fin_dt - fecha_inicio_dt).days + 1
    offset_dia = fecha_inicio_dt.weekday()

    feriados_indices = []
    for f_str in FERIADOS:
        f_dt = datetime.datetime.strptime(f_str, "%Y-%m-%d")
        delta = (f_dt - fecha_inicio_dt).days
        if 0 <= delta < total_dias:
            feriados_indices.append(delta)

    config_turnos, metadata_turnos_raw, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
        servicio_id=SERVICIO_ID, fecha_inicio=FECHA_INICIO, fecha_fin=FECHA_FIN
    )
    empleados = obtener_empleados(SERVICIO_ID, FECHA_INICIO, total_dias)
    turnos_dict = obtener_turnos(SERVICIO_ID)

    # Calculate total demand hours
    total_demand_hours = 0
    
    # We iterate over all days in the block
    for dia in range(total_dias):
        dia_semana = (dia + offset_dia) % 7
        es_finde_o_feriado = (dia_semana >= 5) or (dia in feriados_indices)
        tipo_dia = "Finde_Feriado" if es_finde_o_feriado else "Semana"
        
        # Get demand for this day type
        demandas = demanda_req.get(tipo_dia, [])
        for req in demandas:
            # How many hours is this?
            # It's based on the puesto
            puesto = req.get("puesto")
            # Wait, the demand req gives min/max quantity of people.
            # But what turnos cover this puesto?
            # Let's see: G_Planta (24h), D_Planta (12h), N_Planta (12h) cover the "Planta" puesto.
            # G_Residente (24h), D_Residente (12h), N_Residente (12h) cover "Residente".
            # The demand is in terms of people needed for those roles/shifts.
            # Let's count how many people of each role are needed.
            min_qty = req.get("cantidad_min", 0)
            
            # Let's assume the duration is based on the shift hours
            # Let's check what this demand item corresponds to.
            # Let's print the demand items to understand them:
            print(f"Day {dia} ({tipo_dia}): puesto={puesto}, min={min_qty}")

check_capacity()
