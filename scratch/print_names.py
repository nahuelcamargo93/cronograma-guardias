import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
for row in conn.execute("SELECT nombre FROM personal WHERE nombre LIKE 'Barloa%' OR nombre LIKE 'Godoy%' OR nombre LIKE 'Quintero%'").fetchall():
    print(row[0].encode('utf-8'))
conn.close()
