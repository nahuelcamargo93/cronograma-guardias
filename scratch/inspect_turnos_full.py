import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

print("=== COLUMNAS Y CONTENIDO DE TURNOS_CONFIG SERVICIO 3 ===")
cursor.execute("PRAGMA table_info(turnos_config)")
for col in cursor.fetchall():
    print(col)

cursor.execute("SELECT * FROM turnos_config WHERE servicio_id = 3")
for r in cursor.fetchall():
    print(r)

conn.close()
