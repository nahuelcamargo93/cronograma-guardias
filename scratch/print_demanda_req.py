import sqlite3
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data import FECHA_INICIO, FECHA_FIN, SERVICIO_ID
from database import queries as db_queries

def print_dem():
    config_turnos, metadata_turnos_raw, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
        servicio_id=SERVICIO_ID, fecha_inicio=FECHA_INICIO, fecha_fin=FECHA_FIN
    )
    print("=== Loaded demanda_req ===")
    for tipo_dia, list_req in demanda_req.items():
        print(f"\nTipo Dia: {tipo_dia}")
        for r in list_req:
            print(f"  Puesto ID: {r.get('puesto_id')} | Rango: {r.get('hora_inicio')} - {r.get('hora_fin')} | Min: {r.get('cantidad_min')} | Max: {r.get('cantidad_max')}")

if __name__ == "__main__":
    print_dem()
