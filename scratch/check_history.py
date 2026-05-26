import sys
sys.path.append(".")
import data
from database import queries as db_queries

hist = db_queries.cargar_guardias_previas("2026-06-01", dias_atras=28, servicio_id=3)
print("--- HISTORIAL RETORNADO ---")
for emp, guards in hist.items():
    print(f"Emp: {emp}")
    for g in guards:
        print(f"  {g}")
