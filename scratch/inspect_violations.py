import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

for cid in [261, 262, 263]:
    cursor.execute("SELECT COUNT(*) FROM infracciones_debug WHERE cronograma_id = ?", (cid,))
    count = cursor.fetchone()[0]
    print(f"Crono {cid} tiene {count} infracciones en infracciones_debug")
    if count > 0:
        cursor.execute("SELECT codigo_regla, detalle FROM infracciones_debug WHERE cronograma_id = ? LIMIT 10", (cid,))
        for r in cursor.fetchall():
            print("  -", r)

conn.close()
