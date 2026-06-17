import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

cronograma_id = 253

print("=== ASIGNACIONES DE PLANTA DEL MARTES 7 DE JULIO EN 253 ===")
cursor.execute("""
    SELECT fecha, turno, nombre 
    FROM guardias 
    WHERE cronograma_id = ? AND fecha = '2026-07-07'
      AND (turno LIKE '%Planta%')
    ORDER BY turno
""", (cronograma_id,))
for g in cursor.fetchall():
    print(g)

conn.close()
