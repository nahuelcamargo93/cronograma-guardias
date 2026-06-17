import sqlite3
import os

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "cronograma_inteligente.db"))

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("--- REGISTROS DE MELINA EN PERSONAL ---")
cursor.execute("SELECT * FROM personal WHERE nombre LIKE '%Asutillo%' OR nombre LIKE '%Melina%'")
for row in cursor.fetchall():
    print(row)

print("\n--- REGLAS EN PERSONAL_REGLAS_AJUSTES PARA MELINA ---")
cursor.execute("SELECT * FROM personal_reglas_ajustes WHERE personal_nombre LIKE '%Asutillo%' OR personal_nombre LIKE '%Melina%'")
for row in cursor.fetchall():
    print(row)

conn.close()
