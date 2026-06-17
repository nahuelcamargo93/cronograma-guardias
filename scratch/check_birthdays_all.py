import sqlite3

db_path = r"c:\Users\asus\Desktop\Ryoko\cronograma_inteligente\cronograma_inteligente.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- Todos los cumpleaños registrados en la BD ---")
cursor.execute("SELECT nombre, fecha_cumpleanos, servicio_id FROM personal WHERE fecha_cumpleanos IS NOT NULL AND fecha_cumpleanos != ''")
for r in cursor.fetchall():
    print(r)

conn.close()
