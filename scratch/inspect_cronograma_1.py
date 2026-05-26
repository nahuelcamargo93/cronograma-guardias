import sqlite3
conn = sqlite3.connect("cronograma_inteligente.db")
print("=== CRONOGRAMA 1 ===")
print(conn.execute("SELECT * FROM cronogramas WHERE id = 1").fetchone())
print("=== COUNT OF GUARDIAS FOR CRONOGRAMA 1 ===")
print(conn.execute("SELECT COUNT(*) FROM guardias WHERE cronograma_id = 1").fetchone())
conn.close()
