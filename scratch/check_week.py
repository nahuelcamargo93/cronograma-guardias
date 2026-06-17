import sqlite3

db_path = "cronograma_inteligente.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get latest cronograma id
cursor.execute("SELECT max(id) FROM cronogramas")
crono_id = cursor.fetchone()[0]

print("=== ORTIZ LAURA ===")
cursor.execute("""
    SELECT cronograma_id, fecha, turno, horas 
    FROM guardias 
    WHERE nombre = 'ORTIZ LAURA' AND fecha >= '2026-07-06' AND fecha <= '2026-07-12'
""")
for row in cursor.fetchall():
    print(row)

print("\n=== GOMES STHEFANIA ===")
cursor.execute("""
    SELECT cronograma_id, fecha, turno, horas 
    FROM guardias 
    WHERE nombre = 'GOMES STHEFANIA' AND fecha >= '2026-06-29' AND fecha <= '2026-07-05'
""")
for row in cursor.fetchall():
    print(row)

conn.close()
