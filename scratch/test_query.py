import sqlite3
conn = sqlite3.connect('cronograma_inteligente.db')
query = "SELECT nombre, horas, dias_semana, activo FROM turnos_config WHERE servicio_id = 2"
for row in conn.execute(query).fetchall():
    print(row)
conn.close()
