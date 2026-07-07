import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
print("=== flr_asignados ===")
for r in conn.execute("SELECT * FROM flr_asignados"):
    print(r)
conn.close()
