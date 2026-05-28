import sys
import os
import sqlite3

sys.path.append(os.path.abspath('.'))
from database import queries as db_queries
import rule_engine as _re

db_queries.init_licencias()
reglas_servicio = db_queries.cargar_reglas_servicio(3)
ajustes_reglas = db_queries.cargar_ajustes_reglas_personal("2026-06-01", "2026-06-30")

# Let's get his personal rules
conn = sqlite3.connect("cronograma_inteligente.db")
cur = conn.cursor()
cur.execute("SELECT nombre, servicio_id FROM personal WHERE nombre LIKE '%Mora%'")
row = cur.fetchone()
print(f"Personal: {row}")
name = row[0]

# Load personal rules
cur.execute("""
    SELECT pr.codigo_regla, pr.parametros_json, pr.activo
    FROM personal_reglas pr
    WHERE pr.personal_nombre = ?
""", (name,))
print("\nPersonal rules for Mora:")
for r in cur.fetchall():
    print(r)

# Check resolver_parametros_regla
# We need to pass rules_personal dict
# Let's query rules_personal from database queries module or manually:
from database.data_loader import obtener_empleados
empleados = obtener_empleados(3, "2026-06-01", 30)
emp_mora = next(e for e in empleados if "Mora" in e.nombre)
print(f"\nEmp rules from loader: {emp_mora.reglas}")

p_min = _re.resolver_parametros_regla('MIN_DIA_ESPECIFICO_MES', name, "2026-06-01", reglas_servicio, emp_mora.reglas, ajustes_reglas)
p_exact = _re.resolver_parametros_regla('EXACTO_DIA_ESPECIFICO_MES', name, "2026-06-01", reglas_servicio, emp_mora.reglas, ajustes_reglas)
print(f"\np_min: {p_min}")
print(f"p_exact: {p_exact}")

conn.close()
