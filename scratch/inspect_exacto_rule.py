import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()
cursor.execute("SELECT codigo_regla, parametros_json, activo FROM servicios_reglas WHERE servicio_id = 3")
for row in cursor.fetchall():
    print(f"Regla: {row[0]}")
    print(f"  Activo: {row[2]}")
    print(f"  Params: {row[1]}")
conn.close()
