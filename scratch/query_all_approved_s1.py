import sqlite3

DB_PATH = "cronograma_inteligente.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("--- TODOS LOS CRONOGRAMAS APROBADOS PARA SERVICIO 1 ---")
cursor.execute("""
    SELECT DISTINCT c.id, c.fecha_inicio, c.fecha_fin, c.estado, c.notas
    FROM cronogramas c
    JOIN guardias g ON c.id = g.cronograma_id
    WHERE g.servicio_id = 1 AND c.estado = 'aprobado'
    ORDER BY c.fecha_inicio;
""")
for row in cursor.fetchall():
    print(row)

print("\n--- GUARDIAS EN 2026-06-21 EN CUALQUIER CRONOGRAMA APROBADO (S1) ---")
cursor.execute("""
    SELECT g.cronograma_id, g.nombre, g.fecha, g.turno, g.horas, g.es_finde, c.estado
    FROM guardias g
    JOIN cronogramas c ON g.cronograma_id = c.id
    WHERE g.servicio_id = 1 AND g.fecha = '2026-06-21' AND c.estado = 'aprobado'
    ORDER BY g.nombre;
""")
for row in cursor.fetchall():
    print(row)

conn.close()
