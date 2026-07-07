import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
c = conn.cursor()

c.execute("SELECT id, fecha_inicio, fecha_fin, creado_en, notas, estado, servicio_id FROM cronogramas ORDER BY id DESC LIMIT 20")
rows = c.fetchall()
print("TOP 20 RECENT CRONOGRAMAS IN DB:")
for r in rows:
    print(r)

conn.close()
