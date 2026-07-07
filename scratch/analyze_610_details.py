import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')
c = conn.cursor()

# Get rule config for DISTANCIA_MINIMA_TIPO_SEMANA for service 2
c.execute("SELECT parametros_json, activo FROM servicios_reglas WHERE servicio_id = 2 AND codigo_regla = 'DISTANCIA_MINIMA_TIPO_SEMANA'")
rule_row = c.fetchone()
print("RULE CONFIG FOR DISTANCIA_MINIMA_TIPO_SEMANA (Service 2):")
print(rule_row)

# Get employees in cronograma 610
c.execute("SELECT DISTINCT nombre FROM guardias WHERE cronograma_id = 610")
employees = [r[0] for r in c.fetchall()]
print(f"Employees in 610 ({len(employees)}):", employees[:10], "...")

# Get weeks of cronograma 610 from weeks/semanas_categorias
c.execute("SELECT DISTINCT fecha_lunes FROM semanas_categorias WHERE cronograma_id = 610 ORDER BY fecha_lunes")
weeks = [r[0] for r in c.fetchall()]
print("Weeks in semanas_categorias for 610:", weeks)

conn.close()
