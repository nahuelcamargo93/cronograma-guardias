import sqlite3
import json

DB_PATH = "c:/Users/asus/Desktop/Ryoko/cronograma_inteligente/cronograma_inteligente.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

row = cursor.execute("""
    SELECT parametros_json 
    FROM servicios_reglas 
    WHERE servicio_id = 2 AND codigo_regla = 'MANEJO_FINDES'
""").fetchone()

if row and row[0]:
    print("=== Configuración MANEJO_FINDES Servicio 2 ===")
    parsed = json.loads(row[0])
    print(json.dumps(parsed, indent=2))
else:
    print("No se encontró la regla MANEJO_FINDES para el servicio 2.")

conn.close()
