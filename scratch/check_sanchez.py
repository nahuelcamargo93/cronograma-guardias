import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

print("--- Datos de Sánchez Reinoso, Ana Belén ---")
cursor.execute("SELECT nombre, categoria, rol, regimen_trabajo, horas_mensuales_reglamentarias FROM personal WHERE nombre LIKE '%Sánchez Reinoso%'")
for r in cursor.fetchall():
    print(r)

print("\n--- Reglas de Sánchez Reinoso ---")
cursor.execute("SELECT codigo_regla, parametros_json, activo FROM personal_reglas WHERE personal_nombre LIKE '%Sánchez Reinoso%'")
for r in cursor.fetchall():
    print(r)

print("\n--- Regla general MIN_HORAS_MES_CALENDARIO ---")
cursor.execute("SELECT codigo_regla, parametros_json, activo FROM servicios_reglas WHERE servicio_id = 3 AND codigo_regla = 'MIN_HORAS_MES_CALENDARIO'")
for r in cursor.fetchall():
    print(r)

print("\n--- Guardias asignadas a Sánchez Reinoso en el cronograma 498 (debug) ---")
cursor.execute("SELECT fecha, turno, horas FROM guardias WHERE cronograma_id = 498 AND nombre LIKE '%Sánchez Reinoso%' ORDER BY fecha")
total_horas = 0
for r in cursor.fetchall():
    print(r)
    total_horas += r[2]
print(f"Total horas asignadas: {total_horas}")

conn.close()
