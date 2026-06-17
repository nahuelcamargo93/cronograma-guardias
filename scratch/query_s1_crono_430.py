import sqlite3

DB_PATH = "cronograma_inteligente.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("--- GUARDIAS EN CRONOGRAMA 430 EL 2026-06-21 ---")
cursor.execute("""
    SELECT id, nombre, fecha, turno, horas, es_finde, servicio_id
    FROM guardias
    WHERE cronograma_id = 430 AND fecha = '2026-06-21'
    ORDER BY nombre;
""")
for row in cursor.fetchall():
    print(row)

print("\n--- GUARDIAS DE LEONFORTE O GUARDIA EN CRONOGRAMA 430 ---")
cursor.execute("""
    SELECT id, nombre, fecha, turno, horas, es_finde, servicio_id
    FROM guardias
    WHERE cronograma_id = 430 AND (nombre LIKE '%Leonforte%' OR nombre LIKE '%Guardia%')
    ORDER BY fecha;
""")
for row in cursor.fetchall():
    print(row)

conn.close()
