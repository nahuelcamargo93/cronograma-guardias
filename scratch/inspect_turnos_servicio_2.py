import sqlite3

db_path = "cronograma_inteligente.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=== TURNOS CONFIG SERVICIO 2 ===")
cursor.execute("SELECT id, nombre, hora_inicio, horas, dias_semana, orden, activo FROM turnos_config WHERE servicio_id = 2")
for r in cursor.fetchall():
    print(r)

print("\n=== PUESTOS SERVICIO 2 ===")
cursor.execute("SELECT id, nombre FROM puestos WHERE servicio_id = 2")
for r in cursor.fetchall():
    print(r)

conn.close()
