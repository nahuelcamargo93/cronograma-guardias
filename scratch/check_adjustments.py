import sqlite3
import json

conn = sqlite3.connect("cronograma_inteligente.db")
cursor = conn.cursor()

print("--- Total rows in personal_reglas_ajustes ---")
cursor.execute("SELECT COUNT(*) FROM personal_reglas_ajustes")
print(cursor.fetchone()[0])

print("\n--- Unique codigo_regla in personal_reglas_ajustes ---")
cursor.execute("SELECT DISTINCT codigo_regla FROM personal_reglas_ajustes")
for row in cursor.fetchall():
    print(row)

print("\n--- Sample FRANCO_FORZADO adjustments if any ---")
cursor.execute("SELECT * FROM personal_reglas_ajustes WHERE codigo_regla = 'FRANCO_FORZADO' LIMIT 10")
for row in cursor.fetchall():
    print(row)

print("\n--- Checking columns info ---")
cursor.execute("PRAGMA table_info(personal_reglas_ajustes)")
for col in cursor.fetchall():
    print(col)

conn.close()
