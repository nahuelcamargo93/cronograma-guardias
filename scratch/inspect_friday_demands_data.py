import sys
import os
import json

sys.path.append(os.path.abspath('.'))
from database import queries as db_queries

config_turnos, metadata_turnos_raw, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
    servicio_id=3, fecha_inicio="2026-06-01", fecha_fin="2026-06-30"
)

print("config_turnos keys:")
for k, v in config_turnos.items():
    print(f"  {k}: {list(v.keys())}")

print("\ndemanda_req (Semana):")
for item in demanda_req.get("Semana", []):
    # Friday is weekday 4. Let's see if this item applies to Friday.
    dias_sem = item.get("dias_semana")
    applies_to_friday = False
    if dias_sem:
        dias_validos = [int(x.strip()) for x in dias_sem.split(",") if x.strip().isdigit()]
        if 4 in dias_validos:
            applies_to_friday = True
    else:
        applies_to_friday = True # applies to all weekdays
    
    if applies_to_friday:
        print(f"  ID: {item.get('id')} | Puesto: {item.get('puesto')} | Hora: {item.get('hora_inicio')}-{item.get('hora_fin')} | Min: {item.get('cantidad_min')} | Max: {item.get('cantidad_max')} | Dias: {dias_sem}")

print("\ndemanda_req (Finde_Feriado):")
for item in demanda_req.get("Finde_Feriado", []):
    print(f"  ID: {item.get('id')} | Puesto: {item.get('puesto')} | Hora: {item.get('hora_inicio')}-{item.get('hora_fin')} | Min: {item.get('cantidad_min')} | Max: {item.get('cantidad_max')} | Dias: {item.get('dias_semana')}")
