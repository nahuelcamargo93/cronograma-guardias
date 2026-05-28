import sqlite3
import sys
import os

sys.path.append(os.path.abspath('.'))
from database import queries as db_queries
from database.data_loader import obtener_empleados
import rule_engine as _re

db_queries.init_licencias()
reglas_servicio = db_queries.cargar_reglas_servicio(3)
ajustes_reglas = db_queries.cargar_ajustes_reglas_personal("2026-06-01", "2026-06-30")

conn = sqlite3.connect("cronograma_inteligente.db")
cur = conn.cursor()
cur.execute("SELECT nombre, activo FROM personal WHERE nombre LIKE '%Garcia Rodriguez%'")
row = cur.fetchone()
print(f"Personal: {row}")
name = row[0]

# Check adjustments
cur.execute("SELECT * FROM personal_reglas_ajustes WHERE personal_nombre = ?", (name,))
print("\nAdjustments in DB:")
for r in cur.fetchall():
    print(r)

# Check loader rules
empleados = obtener_empleados(3, "2026-06-01", 30)
emp = next(e for e in empleados if name in e.nombre)
print(f"\nEmp rules: {emp.reglas}")

# Check resolved parameters
p_min = _re.resolver_parametros_regla('MIN_HORAS_MES_CALENDARIO', name, "2026-06-01", reglas_servicio, emp.reglas, ajustes_reglas)
p_max = _re.resolver_parametros_regla('MAX_HORAS_MES_CALENDARIO', name, "2026-06-01", reglas_servicio, emp.reglas, ajustes_reglas)
print(f"p_min: {p_min}")
print(f"p_max: {p_max}")

conn.close()
