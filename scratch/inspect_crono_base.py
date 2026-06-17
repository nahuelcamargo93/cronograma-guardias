import sqlite3

db_path = r"c:\Users\asus\Desktop\Ryoko\cronograma_inteligente\cronograma_inteligente.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- Cronograma 495 ---")
cursor.execute("SELECT * FROM cronogramas WHERE id = 495")
print("Crono 495:", cursor.fetchone())

print("\n--- Cronograma 479 ---")
cursor.execute("SELECT * FROM cronogramas WHERE id = 479")
print("Crono 479:", cursor.fetchone())

print("\n--- Guardias del cronograma 495 (servicio_id) ---")
cursor.execute("SELECT DISTINCT servicio_id FROM guardias WHERE cronograma_id = 495")
print("Servicios en 495:", cursor.fetchall())

print("\n--- Guardias del cronograma 479 (servicio_id) ---")
cursor.execute("SELECT DISTINCT servicio_id FROM guardias WHERE cronograma_id = 479")
print("Servicios en 479:", cursor.fetchall())

conn.close()
