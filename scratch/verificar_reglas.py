import sqlite3
import json

conn = sqlite3.connect("cronograma_inteligente.db")
cursor = conn.cursor()

toledo_nombre = "Toledo, Andrea"
garcia_nombre = "Garcia, Luciano"

print("=== REGLAS BASES ===")
cursor.execute("""
    SELECT personal_nombre, codigo_regla, parametros_json 
    FROM personal_reglas 
    WHERE personal_nombre IN (?, ?)
""", (toledo_nombre, garcia_nombre))
for r in cursor.fetchall():
    print(f"Nombre: {r[0]} | Regla: {r[1]} | Params: {r[2]}")

print("\n=== AJUSTES TEMPORALES (FRANCOS FORZADOS, ETC.) ===")
cursor.execute("""
    SELECT personal_nombre, codigo_regla, fecha_inicio, fecha_fin, parametros_json, activo 
    FROM personal_reglas_ajustes 
    WHERE personal_nombre IN (?, ?) AND activo = 1
""", (toledo_nombre, garcia_nombre))
for r in cursor.fetchall():
    print(f"Nombre: {r[0]} | Regla: {r[1]} | Rango: {r[2]} a {r[3]} | Params: {r[4]}")

conn.close()
