import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
import json
from database.queries import cargar_guardias_previas

res = cargar_guardias_previas("2026-07-01", servicio_id=3)
print(f"Número de personas en historial: {len(res)}")
if res:
    for k, v in list(res.items())[:5]:
        print(k, v)
else:
    print("El historial está vacío.")
