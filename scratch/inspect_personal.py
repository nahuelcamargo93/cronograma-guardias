import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

print("=== feriados de agosto 2026 ===")
cursor.execute("SELECT fecha, descripcion FROM feriados WHERE fecha LIKE '2026-08-%'")
for r in cursor.fetchall():
    print(r)

conn.close()
