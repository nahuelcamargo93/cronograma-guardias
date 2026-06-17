import sqlite3

conn = sqlite3.connect("cronograma_inteligente.db")
cursor = conn.cursor()

# Ver los últimos 15 cronogramas guardados
cursor.execute("""
    SELECT c.id, c.fecha_inicio, c.fecha_fin, c.notas, c.estado, 
           (SELECT count(*) FROM guardias g WHERE g.cronograma_id = c.id) as cant_guardias,
           (SELECT g.servicio_id FROM guardias g WHERE g.cronograma_id = c.id LIMIT 1) as serv_id
    FROM cronogramas c
    ORDER BY c.id DESC
    LIMIT 20;
""")
rows = cursor.fetchall()
print("Últimos cronogramas:")
for r in rows:
    print(f"  ID {r[0]} | {r[1]} a {r[2]} | {r[3]} | Estado: {r[4]} | Guardias: {r[5]} | Servicio_ID: {r[6]}")

conn.close()
