import sqlite3

db_path = "cronograma_inteligente.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

for name in ['Pregot Analia Mariana', 'Zeballos Valeria Alejandra']:
    print(f"\n--- GUARDIAS DE {name} ---")
    cur.execute("""
        SELECT fecha, turno, horas
        FROM guardias
        WHERE cronograma_id = 216 AND nombre = ?
        ORDER BY fecha
    """, (name,))
    total_hours = 0
    for row in cur.fetchall():
        print(f"  {row[0]} | {row[1]} | {row[2]} hs")
        total_hours += row[2]
    print(f"Total hours worked: {total_hours}")

conn.close()
