import sys
import os
import sqlite3
import json

sys.path.append(os.getcwd())

# 1. Update database to 2000 and 500
conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()
cursor.execute("""
    UPDATE servicios_reglas
    SET parametros_json = '{"peso": 2000}'
    WHERE servicio_id = 2 AND regla_id = (SELECT id FROM reglas_catalogo WHERE codigo_regla = 'PESO_EQUIDAD_FINDES_MENSUAL_CALENDARIO')
""")
cursor.execute("""
    UPDATE servicios_reglas
    SET parametros_json = '{"peso": 500}'
    WHERE servicio_id = 2 AND regla_id = (SELECT id FROM reglas_catalogo WHERE codigo_regla = 'PESO_EQUIDAD_FINDES_ANUAL')
""")
conn.commit()
conn.close()

import data
data.FECHA_INICIO = "2026-07-01"
data.FECHA_FIN = "2026-07-31"
data.SERVICIO_ID = 2

import main

print("=== RESOLVING WITH REDUCED WEIGHTS (2000 and 500) ===")
res = main.ejecutar_optimizacion(2, "2026-07-01", "2026-07-31", notas="Test con pesos reducidos")
print("Result:")
print(res)
