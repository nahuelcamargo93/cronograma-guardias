import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.queries import cargar_guardias_previas

res = cargar_guardias_previas("2026-07-01", servicio_id=3)
nesteruk_guardias = res.get('Nesteruk, María Silvia', [])
print("Guardias previas de Nesteruk:")
for g in nesteruk_guardias:
    print(g)
