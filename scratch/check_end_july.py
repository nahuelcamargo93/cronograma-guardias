import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

print("--- Guardias asignadas del 2026-07-25 al 2026-07-31 en el cronograma 498 ---")
cursor.execute("""
    SELECT fecha, nombre, turno, horas 
    FROM guardias 
    WHERE cronograma_id = 498 AND fecha BETWEEN '2026-07-25' AND '2026-07-31'
    ORDER BY fecha, nombre
""")
for r in cursor.fetchall():
    print(r)

conn.close()
