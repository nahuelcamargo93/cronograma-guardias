import sys, os
sys.path.append(os.getcwd())
import database.queries as q
import pprint

reglas = q.cargar_reglas_servicio(1)
print("=== REGLAS DE SERVICIO 1 ===")
pprint.pprint(reglas)
