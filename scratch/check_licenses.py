import sqlite3
conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM licencias")
count = cursor.fetchone()[0]
print(f"Total licencias: {count}")
cursor.execute("SELECT tipo, COUNT(*) FROM licencias GROUP BY tipo")
for row in cursor.fetchall():
    print(row)
conn.close()
