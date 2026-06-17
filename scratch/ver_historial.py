import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

print("--- HISTORIAL DE GUARDIAS PREVIAS (JUNIO 2026) ---")
rows = cursor.execute("""
SELECT g.nombre, g.fecha, g.turno, g.horas
FROM guardias g
JOIN personal p ON g.nombre = p.nombre
WHERE p.servicio_id = 1
  AND g.fecha >= '2026-06-15'
  AND g.fecha <= '2026-06-21'
ORDER BY g.nombre, g.fecha
""").fetchall()
for r in rows:
    print(f"Nombre: {r[0]}, Fecha: {r[1]}, Turno: {r[2]}, Horas: {r[3]}")

conn.close()
