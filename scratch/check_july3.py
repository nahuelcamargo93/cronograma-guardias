import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

print("--- Guardias asignadas el 2026-07-03 en el cronograma 498 ---")
cursor.execute("""
    SELECT nombre, turno, horas 
    FROM guardias 
    WHERE cronograma_id = 498 AND fecha = '2026-07-03'
""")
for r in cursor.fetchall():
    print(r)

print("\n--- Guardias asignadas el 2026-07-09 en el cronograma 498 ---")
cursor.execute("""
    SELECT nombre, turno, horas 
    FROM guardias 
    WHERE cronograma_id = 498 AND fecha = '2026-07-09'
""")
for r in cursor.fetchall():
    print(r)

conn.close()
