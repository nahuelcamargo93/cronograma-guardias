import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
for name_row in conn.execute("SELECT DISTINCT nombre FROM guardias WHERE nombre LIKE '%Florencia%'").fetchall():
    name = name_row[0]
    print("Name:", repr(name))
    print("Length:", len(name))
    print("Char codes:", [ord(c) for c in name])
conn.close()
