import sqlite3
conn = sqlite3.connect('cronograma_inteligente.db')
print("=== FERIADOS DE AGOSTO 2026 ===")
for r in conn.execute("SELECT fecha, descripcion FROM feriados WHERE fecha LIKE '2026-08-%'").fetchall():
    print(r)
