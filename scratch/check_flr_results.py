import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

print("--- FLRS ASIGNADOS EN EL CRONOGRAMA 260 ---")
cursor.execute("SELECT nombre, fecha_inicio, fecha_fin FROM flr_asignados WHERE cronograma_id = 260")
for r in cursor.fetchall():
    print(r)

print("\n--- TODOS LOS EMPLEADOS DEL SERVICIO 2 EN EL CRONOGRAMA 260 ---")
cursor.execute("SELECT DISTINCT nombre FROM guardias WHERE cronograma_id = 260")
crono_emp = [row[0] for row in cursor.fetchall()]
print(f"Total empleados con guardias: {len(crono_emp)}")

cursor.execute("SELECT nombre, fecha_inicio, fecha_fin FROM flr_asignados WHERE cronograma_id = 260")
flr_emp = [row[0] for row in cursor.fetchall()]

sin_flr = [e for e in crono_emp if e not in flr_emp]
print(f"Empleados SIN FLR asignado: {len(sin_flr)}")
for e in sin_flr:
    print(" -", e)

conn.close()
