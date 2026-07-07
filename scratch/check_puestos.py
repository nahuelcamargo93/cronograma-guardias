import sqlite3
import json

conn = sqlite3.connect("cronograma_inteligente.db")
cursor = conn.cursor()

# Ver puestos y sus IDs
print("--- PUESTOS ---")
for row in cursor.execute("SELECT id, nombre, servicio_id FROM puestos WHERE servicio_id = 4").fetchall():
    print(row)

# Ver turnos y sus IDs
print("\n--- TURNOS (servicio 4) ---")
if "turnos" in [r[0] for r in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]:
    for row in cursor.execute("SELECT nombre, horas, puesto_id FROM turnos").fetchall():
        # Vamos a ver si turnos tiene puesto_id u otra cosa, veamos columnas primero:
        cols = [c[1] for c in cursor.execute("PRAGMA table_info(turnos)").fetchall()]
        print("Columnas de turnos:", cols)
        break
    for row in cursor.execute("SELECT * FROM turnos").fetchall():
        print(row)

# Ver personal de servicio 4 con detalle
print("\n--- PERSONAL COMPLETO ---")
personal = cursor.execute("SELECT nombre, categoria, rol, activo FROM personal WHERE servicio_id = 4").fetchall()
for p in personal:
    print(p)

conn.close()
