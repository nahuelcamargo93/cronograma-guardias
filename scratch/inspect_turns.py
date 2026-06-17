import sqlite3
import os

DB_PATH = "cronograma_inteligente.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("--- TURNOS CONFIG SERVICIO 3 ---")
cursor.execute("SELECT id, nombre, hora_inicio, horas, orden, activo, dias_semana, puesto_id FROM turnos_config WHERE servicio_id = 3;")
for row in cursor.fetchall():
    print(row)

print("\n--- CRONOGRAMAS EXISTENTES ---")
cursor.execute("SELECT id, fecha_inicio, fecha_fin, notas, estado, servicio_id FROM cronogramas WHERE servicio_id = 3 OR servicio_id IS NULL;")
for row in cursor.fetchall():
    print(row)

# Let's inspect columns of cronogramas
cursor.execute("PRAGMA table_info(cronogramas);")
print("\n--- CRONOGRAMAS COLUMNS ---")
for col in cursor.fetchall():
    print(col)

conn.close()
