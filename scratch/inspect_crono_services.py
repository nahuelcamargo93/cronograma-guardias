import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

for cid in [261, 262, 263]:
    cursor.execute("""
        SELECT DISTINCT p.servicio_id, s.nombre 
        FROM guardias g
        JOIN personal p ON g.nombre = p.nombre
        JOIN servicios s ON p.servicio_id = s.id
        WHERE g.cronograma_id = ?
    """, (cid,))
    res = cursor.fetchall()
    print(f"Crono {cid}:", res)

conn.close()
