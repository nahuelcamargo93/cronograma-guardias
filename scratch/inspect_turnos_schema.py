import sqlite3
conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(turnos_config)")
print("=== turnos_config schema ===")
for r in cursor.fetchall():
    print(r)
cursor.execute("SELECT * FROM puestos WHERE servicio_id = 1")
print("\n=== puestos service 1 ===")
for r in cursor.fetchall():
    print(r)
conn.close()
