import sqlite3

conn = sqlite3.connect("cronograma_inteligente.db")
cursor = conn.cursor()

print("--- EXCLUSIONES EN PERSONAL_REGLAS_AJUSTES ---")
# Busquemos reglas que parezcan exclusiones de turnos, o veamos todas las reglas distintas en personal_reglas_ajustes
rules = cursor.execute("SELECT DISTINCT codigo_regla FROM personal_reglas_ajustes").fetchall()
print("Reglas distintas en ajustes:", rules)

print("\n--- TURNOS EN LA BD ---")
tables = [r[0] for r in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
if "turnos" in tables:
    cols = [c[1] for c in cursor.execute("PRAGMA table_info(turnos)").fetchall()]
    print("Columnas turnos:", cols)
    rows = cursor.execute("SELECT * FROM turnos").fetchall()
    print("Filas turnos:", rows)

if "puestos" in tables:
    print("\n--- PUESTOS ---")
    print(cursor.execute("SELECT * FROM puestos").fetchall())

conn.close()
