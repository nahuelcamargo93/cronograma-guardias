import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

nombres = ["Lic. Franco", "Lic. Moyano"]

print("=== REGLAS PARTICULARES ===")
cursor.execute("""
    SELECT personal_nombre, codigo_regla, parametros_json, activo
    FROM personal_reglas
    WHERE personal_nombre IN (?, ?)
""", nombres)
for row in cursor.fetchall():
    print(row)

conn.close()
