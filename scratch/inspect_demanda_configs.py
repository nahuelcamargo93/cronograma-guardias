import sqlite3
conn = sqlite3.connect("cronograma_inteligente.db")
conn.row_factory = sqlite3.Row

print("--- PERSONAL IN DATABASE FOR SERVICE 1 ---")
cur = conn.execute("SELECT nombre, categoria, rol, servicio_id FROM personal WHERE servicio_id = 1")
for r in cur:
    print(dict(r))

conn.close()
