import sqlite3
import os

os.chdir(r"c:\Users\asus\Desktop\Ryoko\cronograma_inteligente")
conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

cursor.execute("""
    SELECT personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json 
    FROM personal_reglas_ajustes 
    WHERE personal_nombre IN (SELECT nombre FROM personal WHERE servicio_id = 3)
""")
rows = cursor.fetchall()
for r in rows:
    print(r)

conn.close()
