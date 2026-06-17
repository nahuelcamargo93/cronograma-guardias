import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

print("--- Cronogramas recientes ---")
cursor.execute("SELECT id, fecha_inicio, fecha_fin, estado, creado_en, notas FROM cronogramas ORDER BY id DESC LIMIT 20")
rows = cursor.fetchall()
for r in rows:
    print(r)

print("\n--- Guardias del cronograma 492 ---")
cursor.execute("""
    SELECT g.nombre, g.fecha, g.turno, g.horas, p.servicio_id 
    FROM guardias g
    JOIN personal p ON g.nombre = p.nombre
    WHERE g.cronograma_id = 492
    ORDER BY g.fecha DESC, g.nombre LIMIT 15
""")
for r in cursor.fetchall():
    print(r)

print("\n--- Guardias del cronograma 497 ---")
cursor.execute("""
    SELECT g.nombre, g.fecha, g.turno, g.horas, p.servicio_id 
    FROM guardias g
    JOIN personal p ON g.nombre = p.nombre
    WHERE g.cronograma_id = 497
    ORDER BY g.fecha ASC, g.nombre LIMIT 15
""")
for r in cursor.fetchall():
    print(r)

conn.close()
