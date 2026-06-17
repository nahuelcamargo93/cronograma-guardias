import sqlite3

db_path = r"c:\Users\asus\Desktop\Ryoko\cronograma_inteligente\cronograma_inteligente.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- Personal del servicio_id = 1 con sus datos de Cumpleaños, es_madre, es_padre ---")
cursor.execute("SELECT nombre, fecha_cumpleanos, es_madre, es_padre FROM personal WHERE servicio_id = 1")
for r in cursor.fetchall():
    print(r)

conn.close()
