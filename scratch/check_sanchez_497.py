import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

print("--- Guardias asignadas a Sánchez Reinoso en el cronograma 497 (original) ---")
cursor.execute("SELECT fecha, turno, horas FROM guardias WHERE cronograma_id = 497 AND nombre LIKE '%Sánchez Reinoso%' ORDER BY fecha")
total_horas = 0
for r in cursor.fetchall():
    print(r)
    total_horas += r[2]
print(f"Total horas asignadas: {total_horas}")

conn.close()
