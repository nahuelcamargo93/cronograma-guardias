import sqlite3
conn = sqlite3.connect('cronograma_inteligente.db')
print("=== turnos_config service 1 ===")
for r in conn.execute("SELECT * FROM turnos_config WHERE servicio_id = 1"):
    print(r)
conn.close()
