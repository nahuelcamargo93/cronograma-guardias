import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

print("=== Guardias de Mora, Sergio Enrique en Cronograma 500 ===")
cursor.execute("SELECT fecha, turno, horas FROM guardias WHERE cronograma_id = 500 AND nombre LIKE '%Mora, Sergio%' ORDER BY fecha")
rows = cursor.fetchall()
total_horas = 0
for r in rows:
    print(r)
    total_horas += r[2]
print("Total horas asignadas en Julio:", total_horas)

# Consultar si Mora, Sergio Enrique tiene licencia en Julio
cursor.execute("SELECT tipo, fecha_inicio, fecha_fin FROM licencias WHERE nombre LIKE '%Mora, Sergio%'")
for r in cursor.fetchall():
    print("Licencia de Mora:", r)

conn.close()
