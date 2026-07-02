import database.connection as c
import json

conn = c.get_connection()
tables = ['servicios_reglas', 'personal_reglas', 'servicios_reglas_ajustes', 'personal_reglas_ajustes']
for t in tables:
    print("--- Table:", t)
    rows = conn.execute(f"select * from {t}").fetchall()
    for row in rows:
        row_str = str(row)
        if any(x in row_str for x in ["D_Planta", "N_Planta", "G_Planta", "D_Residente", "N_Residente", "G_Residente"]):
            print(row)
