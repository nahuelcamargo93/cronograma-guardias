import sqlite3

DB_PATH = "c:/Users/asus/Desktop/Ryoko/cronograma_inteligente/cronograma_inteligente.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("=== Licencias Servicio 2 en Julio 2026 ===")
rows = cursor.execute("""
    SELECT l.nombre, l.tipo, l.fecha_inicio, l.fecha_fin
    FROM licencias l
    JOIN personal p ON l.nombre = p.nombre
    WHERE p.servicio_id = 2 AND l.fecha_inicio <= '2026-07-31' AND l.fecha_fin >= '2026-07-01'
    ORDER BY l.nombre, l.fecha_inicio
""").fetchall()

for r in rows:
    print(f"Nombre: {r[0]}, Tipo: {r[1]}, Inicio: {r[2]}, Fin: {r[3]}")

conn.close()
