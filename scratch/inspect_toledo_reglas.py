import sys, os
sys.path.append(os.getcwd())

import sqlite3
import pandas as pd
import rule_engine as _re
import database.queries as q
from database.data_loader import obtener_empleados

servicio_id = 1
fecha_inicio = "2026-08-01"
dias_del_bloque = 31

df = pd.DataFrame(q.obtener_personal_db(servicio_id))
df = q.cargar_datos_personales_bd(df)
ajustes_reglas_personal = q.cargar_ajustes_reglas_personal(fecha_inicio, "2026-08-31")
empleados = obtener_empleados(servicio_id, fecha_inicio, dias_del_bloque)

emp = next(e for e in empleados if e.nombre == 'Toledo, Andrea')

print("=== emp.reglas ===")
import pprint
pprint.pprint(emp.reglas)

print("\n=== ajustes_reglas_personal for Toledo ===")
pprint.pprint(ajustes_reglas_personal.get(emp.nombre))
