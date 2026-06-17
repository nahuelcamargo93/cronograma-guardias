import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

cursor.execute("""
    SELECT id, personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json
    FROM personal_reglas_ajustes
    WHERE personal_nombre LIKE '%Mora%' AND activo = 1
""")

print("=== AJUSTES DE MORA DETALLADOS ===")
for r in cursor.fetchall():
    print(f"ID: {r[0]} | Regla: {r[2]} | Rango: {r[3]} to {r[4]} | Accion: {r[5]} | Params: {r[6]}")

conn.close()
