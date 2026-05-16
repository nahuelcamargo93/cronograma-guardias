import sqlite3
conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(licencias)")
columns = cursor.fetchall()
for col in columns:
    print(col)
conn.close()
