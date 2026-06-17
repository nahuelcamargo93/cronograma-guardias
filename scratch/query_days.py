import sqlite3

DB_PATH = "cronograma_inteligente.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("--- GUARDIAS EN 2026-06-29 Y 2026-06-30 ---")
cursor.execute("""
    SELECT g.id, g.cronograma_id, c.estado, c.notas, g.nombre, g.fecha, g.turno, g.horas, g.es_finde, g.servicio_id
    FROM guardias g
    JOIN cronogramas c ON g.cronograma_id = c.id
    WHERE g.fecha IN ('2026-06-29', '2026-06-30') AND g.servicio_id = 3
    ORDER BY g.fecha, g.nombre;
""")
for row in cursor.fetchall():
    print(row)

conn.close()
