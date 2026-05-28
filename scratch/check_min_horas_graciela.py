import sys
import os
import sqlite3
from datetime import date, timedelta

sys.path.append(os.path.abspath('.'))
from database import queries as db_queries
from database.data_loader import obtener_empleados
import rule_engine as _re

servicio_id = 3
fecha_inicio = "2026-06-01"
fecha_fin = "2026-06-30"
fecha_inicio_dt = date.fromisoformat(fecha_inicio)
dias_del_bloque = (date.fromisoformat(fecha_fin) - fecha_inicio_dt).days + 1

empleados = obtener_empleados(servicio_id, fecha_inicio, dias_del_bloque)
reglas_servicio = db_queries.cargar_reglas_servicio(servicio_id)
ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)

emp = next(e for e in empleados if "Graciela" in e.nombre)
print(f"Employee: {emp.nombre}")

ref_date = fecha_inicio_dt.isoformat()
p_min = _re.resolver_parametros_regla('MIN_HORAS_MES_CALENDARIO', emp.nombre, ref_date, reglas_servicio, emp.reglas, ajustes_reglas)
p_max = _re.resolver_parametros_regla('MAX_HORAS_MES_CALENDARIO', emp.nombre, ref_date, reglas_servicio, emp.reglas, ajustes_reglas)

print(f"p_min: {p_min}")
print(f"p_max: {p_max}")

if _re.regla_existe(p_min) and not _re.regla_suspendida(p_min):
    min_h = p_min.get('min_horas', 144) if isinstance(p_min, dict) else 144
    if not _re.regla_suspendida(p_max):
        max_h_ref = p_max.get('max_horas', 192) if isinstance(p_max, dict) else 192
        if min_h > max_h_ref:
            min_h = max_h_ref
    
    piso = int((min_h / dias_del_bloque) * dias_del_bloque + 0.5)
    print(f"Calculated min_h: {min_h}, piso: {piso}")
else:
    print("Rule MIN_HORAS_MES_CALENDARIO does not exist or is suspended!")

# Let's count hours worked by Aguilera Graciela in Cronograma 215
conn = sqlite3.connect("cronograma_inteligente.db")
cur = conn.cursor()
cur.execute("""
    SELECT SUM(horas)
    FROM guardias
    WHERE cronograma_id = 215 AND nombre = ?
""", (emp.nombre,))
hours_worked = cur.fetchone()[0]
print(f"Hours worked in Cronograma 215: {hours_worked}")

# Let's check all guardias details
cur.execute("""
    SELECT fecha, turno, horas
    FROM guardias
    WHERE cronograma_id = 215 AND nombre = ?
    ORDER BY fecha
""", (emp.nombre,))
print("Guardias list:")
for row in cur.fetchall():
    print(f"  {row[0]} | {row[1]} | {row[2]} hs")
conn.close()
