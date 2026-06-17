import sqlite3

DB_PATH = "c:/Users/asus/Desktop/Ryoko/cronograma_inteligente/cronograma_inteligente.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("=== Infracciones Registradas para Cronograma 319 (Julio) ===")
rows = cursor.execute("""
    SELECT codigo_regla, COUNT(*) 
    FROM infracciones_debug 
    WHERE cronograma_id = 319 
    GROUP BY codigo_regla
""").fetchall()
for r in rows:
    print(f"Regla: {r[0]}, Cantidad de violaciones: {r[1]}")

print("\n=== Muestra de detalles por regla ===")
for r in rows:
    regla = r[0]
    detalles = cursor.execute("""
        SELECT detalle 
        FROM infracciones_debug 
        WHERE cronograma_id = 319 AND codigo_regla = ?
        LIMIT 5
    """, (regla,)).fetchall()
    print(f"\n--- Detalles de {regla} ---")
    for d in detalles:
        print(f"  * {d[0]}")

conn.close()
