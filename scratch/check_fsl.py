import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')
try:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT codigo_regla, parametros_json, activo 
        FROM servicios_reglas 
        WHERE servicio_id = 1
    """)
    for r in cursor.fetchall():
        print(f"Regla: {r[0]}, Activo: {r[2]}")
        print(f"  Parametros: {r[1]}")
finally:
    conn.close()
