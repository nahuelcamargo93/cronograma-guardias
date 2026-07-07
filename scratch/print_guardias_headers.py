import sqlite3
conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.execute("SELECT * FROM guardias LIMIT 1")
names = [d[0] for d in cursor.description]
print("Columns of guardias:", names)
for r in cursor.fetchall():
    print(r)
conn.close()
