import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

print("\n--- Reglas de servicio_id = 2 ---")
cursor.execute("SELECT codigo_regla, activo, parametros_json FROM servicios_reglas WHERE servicio_id = 2 AND codigo_regla LIKE '%FINDE_LARGO%'")
for row in cursor.fetchall():
    print("Código:", row[0])
    print("Activo:", row[1])
    print("JSON:", row[2])
    print("-" * 40)

print("\n--- Catálogo de reglas para FINDE_LARGO ---")
cursor.execute("SELECT codigo_regla, tipo, descripcion FROM reglas_catalogo WHERE codigo_regla LIKE '%FINDE_LARGO%'")
for row in cursor.fetchall():
    print("Código:", row[0])
    print("Tipo:", row[1])
    print("Descripción:", row[2])
    print("-" * 40)

conn.close()
