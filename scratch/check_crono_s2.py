import sqlite3

db_path = 'cronograma_inteligente.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=== Cronogramas aprobados para servicio 2 ===")
rows = cursor.execute("""
    SELECT id, fecha_inicio, fecha_fin, estado, notas
    FROM cronogramas
    WHERE servicio_id = 2 AND estado = 'aprobado'
""").fetchall()

for r in rows:
    print(f"ID: {r[0]}, Inicio: {r[1]}, Fin: {r[2]}, Estado: {r[3]}, Notas: {r[4]}")

print("=== Cronogramas en borrador para servicio 2 en julio ===")
rows_borr = cursor.execute("""
    SELECT id, fecha_inicio, fecha_fin, estado, notas
    FROM cronogramas
    WHERE servicio_id = 2 AND fecha_inicio = '2026-07-01'
""").fetchall()

for r in rows_borr:
    print(f"ID: {r[0]}, Inicio: {r[1]}, Fin: {r[2]}, Estado: {r[3]}, Notas: {r[4]}")

conn.close()
