import sqlite3

db_path = r"c:\Users\asus\Desktop\Ryoko\cronograma_inteligente\cronograma_inteligente.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- Licencias del servicio 1 en Junio 2026 ---")
cursor.execute("""
    SELECT l.nombre, l.tipo, l.fecha_inicio, l.fecha_fin 
    FROM licencias l
    JOIN personal p ON l.nombre = p.nombre
    WHERE p.servicio_id = 1 AND l.fecha_inicio <= '2026-06-30' AND l.fecha_fin >= '2026-06-22'
""")
for r in cursor.fetchall():
    print(r)

conn.close()
