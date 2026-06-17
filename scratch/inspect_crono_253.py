import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

cronograma_id = 253

print("=== CRONOGRAMA 253 ===")
cursor.execute("SELECT id, fecha_inicio, fecha_fin, notas FROM cronogramas WHERE id = ?", (cronograma_id,))
print("Cronograma:", cursor.fetchone())

# Guardias de Aguilera Graciela y Garcia Rodriguez en el cronograma 253
cursor.execute("""
    SELECT fecha, nombre, turno, horas 
    FROM guardias 
    WHERE cronograma_id = ? AND (nombre = 'Aguilera Graciela' OR nombre LIKE '%Garcia Rodriguez%')
    ORDER BY fecha, nombre
""", (cronograma_id,))
print("\nGuardias de Aguilera y Garcia Rodriguez en 253:")
for g in cursor.fetchall():
    print(g)


# Ver las asignaciones del 20 al 27 de julio para Planta en 253
print("\n=== ASIGNACIONES DE PLANTA DEL 20 AL 27 DE JULIO EN 253 ===")
cursor.execute("""
    SELECT fecha, turno, nombre 
    FROM guardias 
    WHERE cronograma_id = ? AND fecha BETWEEN '2026-07-20' AND '2026-07-27'
      AND (turno LIKE '%Planta%')
    ORDER BY fecha, turno
""", (cronograma_id,))
for g in cursor.fetchall():
    print(g)

conn.close()
