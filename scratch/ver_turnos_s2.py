import sqlite3

DB_PATH = "c:/Users/asus/Desktop/Ryoko/cronograma_inteligente/cronograma_inteligente.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("=== Columns of turnos_config ===")
cursor.execute("PRAGMA table_info(turnos_config)")
for col in cursor.fetchall():
    print(col)

print("\n=== Rows of turnos_config Servicio 2 ===")
rows = cursor.execute("SELECT * FROM turnos_config WHERE servicio_id = 2 AND activo = 1").fetchall()
for r in rows:
    print(r)

conn.close()
