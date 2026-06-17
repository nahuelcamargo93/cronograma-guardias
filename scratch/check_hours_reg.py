import sqlite3

conn = sqlite3.connect("cronograma_inteligente.db")
rows = conn.execute("SELECT nombre, rol, horas_mensuales_reglamentarias, regimen_trabajo FROM personal WHERE servicio_id = 1").fetchall()
for r in rows:
    print(f"Nombre: {r[0]}, Rol: {r[1]}, Horas Reg: {r[2]}, Regimen: {r[3]}")
conn.close()
