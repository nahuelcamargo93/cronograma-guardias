import sqlite3
conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

cursor.execute("""
    SELECT DISTINCT c.id, c.fecha_inicio, c.fecha_fin, c.estado, c.notas
    FROM cronogramas c
    JOIN guardias g ON c.id = g.cronograma_id
    JOIN personal p ON g.nombre = p.nombre
    WHERE p.servicio_id = 3 AND c.estado = 'aprobado'
    ORDER BY c.fecha_inicio DESC
""")
print("Cronogramas aprobados para servicio 3:")
for r in cursor.fetchall():
    print(r)

print("\n¿Cuántas guardias tiene el cronograma 492 por fecha?")
cursor.execute("""
    SELECT fecha, COUNT(*) 
    FROM guardias 
    WHERE cronograma_id = 492 
    GROUP BY fecha 
    ORDER BY fecha
""")
for r in cursor.fetchall():
    print(r)

conn.close()
