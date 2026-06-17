import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

print("=== Reglas de Mora, Sergio Enrique en personal_reglas ===")
cursor.execute("SELECT codigo_regla, parametros_json, activo FROM personal_reglas WHERE personal_nombre LIKE '%Mora, Sergio%'")
for r in cursor.fetchall():
    print(r)

print("\n=== Ajustes de Reglas de Mora en personal_reglas_ajustes ===")
cursor.execute("SELECT codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json FROM personal_reglas_ajustes WHERE personal_nombre LIKE '%Mora, Sergio%'")
for r in cursor.fetchall():
    print(r)

conn.close()
