import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

cronograma_id = 253

print("=== HORAS DE MEDICOS DE PLANTA EN CRONOGRAMA 253 ===")
cursor.execute("""
    SELECT g.nombre, SUM(g.horas) as horas_totales
    FROM guardias g
    JOIN personal p ON g.nombre = p.nombre
    WHERE g.cronograma_id = ? AND p.servicio_id = 3
    GROUP BY g.nombre
    ORDER BY horas_totales DESC
""", (cronograma_id,))
for r in cursor.fetchall():
    print(r)

# Ver las infracciones de MIN_HORAS_MES_CALENDARIO para todos en 253
print("\n=== VIOLACIONES DE MIN_HORAS EN 253 ===")
cursor.execute("""
    SELECT codigo_regla, detalle 
    FROM infracciones_debug 
    WHERE cronograma_id = ? AND codigo_regla = 'MIN_HORAS_MES_CALENDARIO'
""", (cronograma_id,))
for inf in cursor.fetchall():
    print(inf)

conn.close()
