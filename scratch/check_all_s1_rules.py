import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

cursor.execute("""
    SELECT codigo_regla, activo, parametros_json 
    FROM servicios_reglas 
    WHERE servicio_id = 1
""")
rows = cursor.fetchall()
print("=== REGLAS CONFIGURADAS PARA SERVICIO 1 ===")
for code, active, params in rows:
    print(f"Regla: {code} | Activo: {active} | Params: {params}")

conn.close()
