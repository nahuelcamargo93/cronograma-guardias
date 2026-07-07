import sqlite3
conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()
rows = cursor.execute("SELECT nombre, sigla FROM turnos_config WHERE servicio_id = 2").fetchall()
print("Siglas para servicio 2:")
for r in rows:
    print(r)
conn.close()
