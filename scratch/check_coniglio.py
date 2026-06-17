import sqlite3

db_path = "cronograma_inteligente.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Ver reglas en personal_reglas_ajustes
print("--- Ajustes de Coniglio, Melisa en personal_reglas_ajustes ---")
cursor.execute("""
    SELECT id, personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo
    FROM personal_reglas_ajustes
    WHERE personal_nombre LIKE '%Coniglio%'
""")
for r in cursor.fetchall():
    print(r)

conn.close()
