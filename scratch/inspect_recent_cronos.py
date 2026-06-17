import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

print("--- Últimos 20 cronogramas en la BD ---")
cursor.execute("""
    SELECT c.id, c.fecha_inicio, c.fecha_fin, c.creado_en, c.notas, c.estado 
    FROM cronogramas c
    ORDER BY c.id DESC
    LIMIT 20
""")
for r in cursor.fetchall():
    print(r)

conn.close()
