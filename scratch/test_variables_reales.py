import sqlite3

db_path = "c:\\Users\\asus\\Desktop\\Ryoko\\cronograma_inteligente\\cronograma_inteligente.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=== INFRACCIONES DETECTADAS (Cronograma 519) ===")
rows = cursor.execute("""
    SELECT codigo_regla, detalle
    FROM infracciones_debug
    WHERE cronograma_id = 519
""").fetchall()

for r in rows:
    print(f"Regla: {r[0]} | Detalle: {r[1]}")

conn.close()
