import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
conn.execute("UPDATE cronogramas SET estado = 'aprobado' WHERE id = 492")
conn.commit()
r = conn.execute("SELECT id, estado FROM cronogramas WHERE id = 492").fetchone()
print("492 estado:", r)
conn.close()
