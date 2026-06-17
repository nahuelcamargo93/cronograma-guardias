import sqlite3
import os

db_path = "cronograma_inteligente.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- Turnos activos del servicio 1 ---")
cursor.execute("SELECT nombre, hora_inicio, horas, dias_semana FROM turnos_config WHERE servicio_id = 1 AND activo = 1")
for row in cursor.fetchall():
    print(f"Nombre: {row[0]} | Hora Inicio: {row[1]} | Horas: {row[2]} | Dias Semana: {row[3]}")

conn.close()
