import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

cursor.execute("SELECT nombre, regimen_trabajo, horas_mensuales_reglamentarias FROM personal WHERE servicio_id = 2")
rows = cursor.fetchall()
print("PERSONAL CONTRACT HOURS FOR SERVICE 2:")
for r in rows:
    print(f"  Name: {r[0]:25s} | Regimen: {r[1]} | Horas Reglamentarias: {r[2]}")

conn.close()
