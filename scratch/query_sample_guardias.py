import sqlite3

DB_PATH = "cronograma_inteligente.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("--- ALGUNAS GUARDIAS DE EJEMPLO DEL SERVICIO 3 EN JUNIO 2026 ---")
cursor.execute("""
    SELECT DISTINCT nombre, fecha, turno, horas, es_finde
    FROM guardias
    WHERE servicio_id = 3 AND fecha BETWEEN '2026-06-01' AND '2026-06-30'
    ORDER BY fecha, nombre
    LIMIT 40;
""")
for row in cursor.fetchall():
    print(row)

conn.close()
