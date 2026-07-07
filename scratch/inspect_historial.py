import sqlite3
from datetime import date, timedelta

db_path = 'cronograma_inteligente.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Buscar guardias del 2026-07-27 al 2026-07-31 para el servicio 2
print("=== Guardias previas en la semana de transición (27 al 31 de julio de 2026) ===")
rows = cursor.execute("""
    SELECT g.nombre, g.fecha, g.turno, c.id, c.estado
    FROM guardias g
    JOIN cronogramas c ON g.cronograma_id = c.id
    JOIN personal p ON g.nombre = p.nombre
    WHERE p.servicio_id = 2 AND g.fecha BETWEEN '2026-07-27' AND '2026-07-31'
    ORDER BY g.nombre, g.fecha
""").fetchall()

for r in rows:
    print(f"Empleado: {r[0]}, Fecha: {r[1]}, Turno: {r[2]}, Crono ID: {r[3]}, Estado: {r[4]}")

conn.close()
