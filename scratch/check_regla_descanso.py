import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

cursor.execute("SELECT codigo_regla, parametros_json, activo FROM servicios_reglas WHERE servicio_id = 3 AND codigo_regla = 'DESCANSO_ENTRE_TURNOS'")
row = cursor.fetchone()
if row:
    print("Código regla:", row[0])
    print("Activo:", row[2])
    print("JSON:", json.loads(row[1]) if row[1] else "None")
else:
    print("Regla DESCANSO_ENTRE_TURNOS no encontrada para el servicio 3.")

conn.close()
