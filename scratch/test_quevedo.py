import sqlite3

conn = sqlite3.connect("cronograma_inteligente.db")
cursor = conn.cursor()

cursor.execute("""
    SELECT cronograma_id, fecha, turno, horas 
    FROM guardias 
    WHERE nombre = 'QUEVEDO CELESTE' AND cronograma_id IN (301, 302) AND fecha IN ('2026-07-09', '2026-07-10')
""")
print("Guardias de QUEVEDO CELESTE en feriados de Julio 2026 (crono 301 y 302):")
for r in cursor.fetchall():
    print(r)

conn.close()
