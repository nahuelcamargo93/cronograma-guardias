import sqlite3
import os

DB_PATH = "cronograma_inteligente.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("Rules for Service 3:")
cursor.execute("""
    SELECT rc.codigo_regla 
    FROM servicios_reglas sr 
    JOIN reglas_catalogo rc ON sr.regla_id = rc.id 
    WHERE sr.servicio_id = 3
""")
for row in cursor.fetchall():
    print(row[0])

conn.close()
