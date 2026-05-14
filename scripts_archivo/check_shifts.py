import sqlite3
conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()
cursor.execute("SELECT nombre FROM turnos_config WHERE servicio_id = 2")
print([r[0] for r in cursor.fetchall()])
conn.close()
