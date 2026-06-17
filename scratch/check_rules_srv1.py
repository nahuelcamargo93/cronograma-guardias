import sqlite3
import os
import json

db_path = r"c:\Users\asus\Desktop\Ryoko\cronograma_inteligente\cronograma_inteligente.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- Reglas en servicios_reglas para servicio_id = 1 ---")
cursor.execute("SELECT * FROM servicios_reglas WHERE servicio_id = 1")
rows = cursor.fetchall()
for r in rows:
    print(r)

print("\n--- Estado de las reglas específicas CUMPLEANOS_LIBRE y DIA_MADRE_PADRE_LIBRE en reglas_catalogo ---")
cursor.execute("SELECT * FROM reglas_catalogo WHERE codigo_regla IN ('CUMPLEANOS_LIBRE', 'DIA_MADRE_PADRE_LIBRE')")
for r in cursor.fetchall():
    print(r)

print("\n--- Reglas en servicios_reglas para estas reglas específicas para cualquier servicio ---")
cursor.execute("SELECT * FROM servicios_reglas WHERE codigo_regla IN ('CUMPLEANOS_LIBRE', 'DIA_MADRE_PADRE_LIBRE')")
for r in cursor.fetchall():
    print(r)

conn.close()
