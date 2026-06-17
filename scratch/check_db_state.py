import sqlite3
conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

cursor.execute("SELECT id, fecha_inicio, fecha_fin, estado, notas FROM cronogramas WHERE id IN (37, 492, 497)")
print("Estado de los cronogramas en conflicto:")
for r in cursor.fetchall():
    print(r)

conn.close()
