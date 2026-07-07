import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
print("=== cronogramas ===")
for r in conn.execute("SELECT id, fecha_inicio, fecha_fin, creado_en, notas, estado FROM cronogramas ORDER BY id DESC LIMIT 20"):
    print(r)
conn.close()
