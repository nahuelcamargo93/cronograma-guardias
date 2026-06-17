import sqlite3
import os

DB_PATH = "c:/Users/asus/Desktop/Ryoko/cronograma_inteligente/cronograma_inteligente.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("=== Puestos del Servicio 2 ===")
puestos = cursor.execute("SELECT id, nombre FROM puestos WHERE servicio_id = 2").fetchall()
for p in puestos:
    print(f"ID: {p[0]}, Nombre: {p[1]}")

print("\n=== Turnos del Servicio 2 ===")
turnos = cursor.execute("SELECT id, nombre, horas, hora_inicio, puesto_id FROM turnos_config WHERE servicio_id = 2 AND activo = 1").fetchall()
for t in turnos:
    print(f"ID: {t[0]}, Nombre: {t[1]}, Horas: {t[2]}, Inicio: {t[3]}, Puesto ID: {t[4]}")

conn.close()
