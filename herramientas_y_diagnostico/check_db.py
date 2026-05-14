import sqlite3
conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()
cursor.execute("SELECT id, nombre FROM turnos_config")
for row in cursor.fetchall():
    print(row)
conn.close()
