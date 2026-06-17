import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

cronograma_id = 253

# Buscar las reglas de Moya Pedro y Biscarra Joaquín Martín
print("=== REGLAS DE MOYA PEDRO ===")
cursor.execute("""
    SELECT pr.id, pr.codigo_regla, pr.parametros_json 
    FROM personal_reglas pr
    WHERE pr.personal_nombre LIKE '%Moya%'
""")
for r in cursor.fetchall():
    print(r)

print("\n=== REGLAS DE BISCARRA JOAQUIN ===")
cursor.execute("""
    SELECT pr.id, pr.codigo_regla, pr.parametros_json 
    FROM personal_reglas pr
    WHERE pr.personal_nombre LIKE '%Biscarra%'
""")
for r in cursor.fetchall():
    print(r)

# Ver las guardias de Moya y Biscarra en el cronograma 253
print("\n=== GUARDIAS DE MOYA EN 253 ===")
cursor.execute("""
    SELECT fecha, turno, horas 
    FROM guardias 
    WHERE cronograma_id = ? AND nombre LIKE '%Moya%'
    ORDER BY fecha
""", (cronograma_id,))
for g in cursor.fetchall():
    print(g)

print("\n=== GUARDIAS DE BISCARRA EN 253 ===")
cursor.execute("""
    SELECT fecha, turno, horas 
    FROM guardias 
    WHERE cronograma_id = ? AND nombre LIKE '%Biscarra%'
    ORDER BY fecha
""", (cronograma_id,))
for g in cursor.fetchall():
    print(g)

conn.close()
