import sqlite3
import os

TEMP_DB = "temp_unsat_core.db"
if os.path.exists(TEMP_DB):
    conn = sqlite3.connect(TEMP_DB)
    rows = conn.execute("SELECT * FROM personal_reglas_ajustes WHERE personal_nombre = 'SUAREZ Carolina'").fetchall()
    print("=== personal_reglas_ajustes FOR SUAREZ Carolina in temp DB ===")
    for r in rows:
        print(r)
    conn.close()
else:
    print("Temp DB does not exist.")
