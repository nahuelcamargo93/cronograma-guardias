import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

cursor.execute("SELECT codigo_regla, detalle FROM infracciones_debug WHERE cronograma_id = 498")
print("Infracciones detectadas para cronograma 498:")
for r in cursor.fetchall():
    print(r)

conn.close()
