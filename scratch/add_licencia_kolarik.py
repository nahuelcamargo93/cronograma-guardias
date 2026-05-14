import sqlite3
import os

os.chdir(r"c:\Users\asus\Desktop\Ryoko\cronograma_inteligente")
conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

nombre = 'Kolarik Jorge Luis'
cursor.execute("DELETE FROM licencias WHERE nombre = ? AND tipo = 'LM'", (nombre,))
cursor.execute("INSERT INTO licencias (nombre, tipo, fecha_inicio, fecha_fin) VALUES (?, 'LM', '2026-06-01', '2026-12-31')", (nombre,))

conn.commit()
print(f"Licencia LM añadida para {nombre}.")
conn.close()
