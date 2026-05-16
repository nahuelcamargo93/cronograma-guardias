import sqlite3
import os

DB_PATH = "cronograma_inteligente.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("Fathers in Service 3:")
cursor.execute("""
    SELECT nombre, es_padre, fecha_cumpleanos 
    FROM personal 
    WHERE servicio_id = 3 AND (es_padre = 1 OR fecha_cumpleanos LIKE '%-06-%')
""")
for row in cursor.fetchall():
    print(f"Name: {row[0]}, Father: {row[1]}, BDay: {row[2]}")

conn.close()
