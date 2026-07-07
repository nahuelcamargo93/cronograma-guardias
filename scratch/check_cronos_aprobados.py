import sqlite3

db_path = 'cronograma_inteligente.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=== Cronogramas en la base de datos ===")
rows = cursor.execute("""
    SELECT id, fecha_inicio, fecha_fin, estado, notas, servicio_id
    FROM cronogramas
    ORDER BY id DESC
""").fetchall()

for r in rows:
    print(f"ID: {r[0]}, Inicio: {r[1]}, Fin: {r[2]}, Estado: {r[3]}, Notas: {r[4]}, Servicio: {r[5]}")

conn.close()
