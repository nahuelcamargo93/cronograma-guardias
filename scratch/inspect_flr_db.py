import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

print("--- REGLAS EN EL CATALOGO ---")
cursor.execute("SELECT id, codigo_regla, tipo, descripcion FROM reglas_catalogo WHERE codigo_regla LIKE '%FINDE_LARGO%'")
for r in cursor.fetchall():
    print(r)

print("\n--- REGLAS DE SERVICIO 2 ---")
cursor.execute("SELECT id, servicio_id, codigo_regla, parametros_json, activo FROM servicios_reglas WHERE servicio_id = 2 AND codigo_regla LIKE '%FINDE_LARGO%'")
for r in cursor.fetchall():
    print(r)

conn.close()
