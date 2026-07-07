import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
c = conn.cursor()

c.execute("PRAGMA table_info(turnos_config)")
print("Columns in turnos_config:")
print(c.fetchall())

c.execute("SELECT nombre, activo, solo_importacion FROM turnos_config WHERE servicio_id = 2")
print("\nTurnos configuration:")
for r in c.fetchall():
    print(r)

conn.close()
