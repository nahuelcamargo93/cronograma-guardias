import sqlite3

DB_PATH = "cronograma_inteligente.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("--- GUARDIAS EN CRONOGRAMA 494 PARA EL 2026-06-22 ---")
cursor.execute("""
    SELECT fecha, nombre, turno, horas, es_finde, servicio_id
    FROM guardias
    WHERE cronograma_id = 494 AND fecha = '2026-06-22'
    ORDER BY turno, nombre;
""")
for row in cursor.fetchall():
    print(row)

conn.close()
