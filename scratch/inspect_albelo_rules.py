import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

print("--- REGLAS EN PERSONAL_REGLAS PARA ALBELO TANIA ---")
cursor.execute("SELECT codigo_regla, parametros_json, activo FROM personal_reglas WHERE personal_nombre = 'ALBELO TANIA'")
for r in cursor.fetchall():
    print(r)

print("\n--- AJUSTES PARA ALBELO TANIA EN EL PERIODO JULIO 2026 ---")
# Buscamos en personal_reglas_ajustes si existe (o como se llame la tabla de ajustes)
# Veamos qué tablas de ajustes existen
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print("Tablas en la BD:", tables)

if 'personal_reglas_ajustes' in tables:
    cursor.execute("SELECT * FROM personal_reglas_ajustes WHERE personal_nombre = 'ALBELO TANIA'")
    for r in cursor.fetchall():
        print(r)

conn.close()
