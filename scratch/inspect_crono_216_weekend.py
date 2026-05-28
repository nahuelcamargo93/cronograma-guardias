import sqlite3

db_path = "cronograma_inteligente.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Get guardias on June 13, 14, 15 in cronograma 216
cur.execute("""
    SELECT g.fecha, g.turno, g.nombre, p.rol
    FROM guardias g
    JOIN personal p ON g.nombre = p.nombre
    WHERE g.cronograma_id = 216 AND g.fecha IN ('2026-06-13', '2026-06-14', '2026-06-15')
    ORDER BY g.fecha, g.turno
""")
print("Assignments on June 13-15 in Cronograma 216:")
for row in cur.fetchall():
    print(row)

conn.close()
