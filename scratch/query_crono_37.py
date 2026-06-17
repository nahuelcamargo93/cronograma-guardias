import sqlite3

DB_PATH = "cronograma_inteligente.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
    SELECT COUNT(*) FROM guardias WHERE cronograma_id = 37;
""")
print("Total guardias in cronograma 37:", cursor.fetchone()[0])

cursor.execute("""
    SELECT nombre, fecha, turno, horas, es_finde, servicio_id
    FROM guardias
    WHERE cronograma_id = 37 AND fecha IN ('2026-06-29', '2026-06-30')
    ORDER BY fecha, nombre;
""")
print("\nGuardias in cronograma 37 for 2026-06-29 and 2026-06-30:")
for r in cursor.fetchall():
    print(r)

conn.close()
