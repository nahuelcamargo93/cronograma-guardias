import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

print("=== ALL HISTORICAL GUARDS FOR MAY 2026 ===")
cursor.execute("""
    SELECT g.fecha, g.nombre, g.turno, g.horas, c.id, c.estado
    FROM guardias g
    JOIN cronogramas c ON g.cronograma_id = c.id
    WHERE g.fecha >= '2026-05-25' AND g.fecha <= '2026-05-31'
    ORDER BY g.fecha, g.nombre
""")
for r in cursor.fetchall():
    print(r)

print("\n=== CALENDARIO ASOCIADO A JUNIO ===")
cursor.execute("SELECT * FROM calendario WHERE id = 137")
print(cursor.fetchall())

conn.close()
