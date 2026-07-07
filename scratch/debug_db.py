import sqlite3
import os

db_path = "cronograma_inteligente.db"
print("DB size:", os.path.getsize(db_path))

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=== ultimos 10 cronogramas ===")
cursor.execute("SELECT id, servicio_id, fecha_inicio, creado_en, notas FROM cronogramas ORDER BY id DESC LIMIT 10")
for r in cursor.fetchall():
    print(r)

print("\n=== buscando id = 597 ===")
cursor.execute("SELECT id, servicio_id, fecha_inicio, creado_en, notas FROM cronogramas WHERE id = 597")
print(cursor.fetchone())

conn.close()
