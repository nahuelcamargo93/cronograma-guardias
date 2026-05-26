import sys
import os
sys.path.append(os.getcwd())

import data
data.FECHA_INICIO = "2026-07-01"
data.FECHA_FIN = "2026-07-31"
data.SERVICIO_ID = 2

import main

print("=== RESOLVING JULY 2026 NURSING SCHEDULE ===")
res = main.ejecutar_optimizacion(2, "2026-07-01", "2026-07-31", notas="Generado optimizado via script")
print("Optimization result:")
print(res)
