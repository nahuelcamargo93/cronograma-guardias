import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
c = conn.cursor()

c.execute("SELECT id, fecha_inicio, fecha_fin, creado_en, notas, estado, servicio_id FROM cronogramas WHERE estado = 'aprobado' ORDER BY fecha_inicio DESC")
rows = c.fetchall()
print("APPROVED CRONOGRAMAS:")
for r in rows:
    print(r)

conn.close()
