import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

print("--- Parámetros de la regla DESCANSO_ENTRE_TURNOS para servicio 3 ---")
cursor.execute("""
    SELECT codigo_regla, parametros_json, activo 
    FROM servicios_reglas 
    WHERE servicio_id = 3 AND codigo_regla = 'DESCANSO_ENTRE_TURNOS'
""")
for r in cursor.fetchall():
    print(r)

print("\n--- Reglas personales para Zeballos ---")
cursor.execute("""
    SELECT personal_nombre, codigo_regla, parametros_json, activo 
    FROM personal_reglas 
    WHERE personal_nombre LIKE '%Zeballos%' AND activo = 1
""")
for r in cursor.fetchall():
    print(r)

conn.close()
