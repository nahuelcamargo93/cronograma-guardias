import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cronograma_inteligente.db")
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

print("--- PUESTOS ---")
puestos = conn.execute("SELECT * FROM puestos WHERE servicio_id = 1").fetchall()
for p in puestos:
    print(dict(p))

print("\n--- TURNOS CONFIG ---")
turnos = conn.execute("SELECT * FROM turnos_config WHERE servicio_id = 1").fetchall()
for t in turnos:
    print(dict(t))

print("\n--- REGISTROS CONIGLIO ---")
personal = conn.execute("SELECT * FROM personal WHERE nombre LIKE '%Coniglio%'").fetchall()
for p in personal:
    print(dict(p))

print("\n--- REGLAS ASIGNACION_FIJA CONIGLIO ---")
reglas = conn.execute("SELECT * FROM personal_reglas WHERE personal_nombre LIKE '%Coniglio%'").fetchall()
for r in reglas:
    print(dict(r))

print("\n--- AJUSTES REGLAS CONIGLIO ---")
ajustes = conn.execute("SELECT * FROM personal_reglas_ajustes WHERE personal_nombre LIKE '%Coniglio%'").fetchall()
for a in ajustes:
    print(dict(a))

conn.close()
