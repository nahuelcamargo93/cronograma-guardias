import sqlite3

DB_PATH = "cronograma_inteligente.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
    SELECT DISTINCT c.id, c.fecha_inicio, c.fecha_fin, c.estado, c.notas
    FROM cronogramas c
    JOIN guardias g ON c.id = g.cronograma_id
    WHERE g.servicio_id = 3 AND c.fecha_inicio = '2026-06-01' AND c.fecha_fin = '2026-06-30' AND c.estado = 'aprobado';
""")
rows = cursor.fetchall()
print("Aprobado June 2026 cronogramas for service 3:")
for r in rows:
    print(r)

conn.close()
