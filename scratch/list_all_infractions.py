import sqlite3
conn = sqlite3.connect('cronograma_inteligente.db')
rows = conn.execute("SELECT codigo_regla, detalle FROM infracciones_debug WHERE cronograma_id=334").fetchall()
for r in rows:
    print(f"{r[0]}: {r[1]}")
conn.close()
