import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

nombres = ["Lic. Garcia", "Lic. Toledo"]

print("=== LICENCIAS ===")
cursor.execute("""
    SELECT nombre, tipo, fecha_inicio, fecha_fin 
    FROM licencias 
    WHERE nombre IN (?, ?)
""", nombres)
for row in cursor.fetchall():
    print(row)

print("\n=== AJUSTES DE REGLAS TEMPORALES ===")
cursor.execute("""
    SELECT personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo
    FROM personal_reglas_ajustes
    WHERE personal_nombre IN (?, ?)
""", nombres)
for row in cursor.fetchall():
    print(row)

print("\n=== REGLAS PARTICULARES ===")
cursor.execute("""
    SELECT personal_nombre, codigo_regla, parametros_json, activo
    FROM personal_reglas
    WHERE personal_nombre IN (?, ?)
""", nombres)
for row in cursor.fetchall():
    print(row)

conn.close()
