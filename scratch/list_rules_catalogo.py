import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

print("=== ALL CATALOG RULES (reglas_catalogo) ===")
cursor.execute("SELECT id, codigo_regla, tipo, descripcion FROM reglas_catalogo ORDER BY codigo_regla")
for r in cursor.fetchall():
    print(r)

conn.close()
