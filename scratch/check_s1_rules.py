import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

cursor.execute("""
    SELECT parametros_json 
    FROM servicios_reglas 
    WHERE servicio_id = 1 AND codigo_regla = 'MANEJO_FINDES'
""")
row = cursor.fetchone()
if row:
    print("=== CONFIGURACIÓN ACTUAL EN BD ===")
    print(row[0])
else:
    print("No se encontró la regla MANEJO_FINDES para el servicio 1.")

conn.close()
