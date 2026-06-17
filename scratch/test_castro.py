import sqlite3

conn = sqlite3.connect("cronograma_inteligente.db")
cursor = conn.cursor()

# Guardias de CASTRO LUCIANO en cronogramas 301 y 302
cursor.execute("""
    SELECT cronograma_id, fecha, turno, horas 
    FROM guardias 
    WHERE nombre = 'CASTRO LUCIANO' AND cronograma_id IN (301, 302)
    ORDER BY fecha;
""")
rows = cursor.fetchall()
print("Guardias de CASTRO LUCIANO en 301 y 302:")
for r in rows:
    print(r)

# Ver las fechas de los feriados de Julio 2026
cursor.execute("SELECT fecha, descripcion FROM feriados WHERE fecha LIKE '2026-07%';")
print("\nFeriados de Julio 2026:")
for r in cursor.fetchall():
    print(r)

conn.close()
