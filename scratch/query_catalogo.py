import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

cursor.execute("""
    SELECT codigo_regla, tipo, descripcion 
    FROM reglas_catalogo 
    WHERE codigo_regla LIKE '%FINDE%' OR codigo_regla LIKE '%FLR%' OR codigo_regla LIKE '%LARGO%'
""")
rows = cursor.fetchall()
print("=== REGLAS EN CATALOGO ===")
for code, tipo, desc in rows:
    print(f"Regla: {code} | Tipo: {tipo} | Desc: {desc}")

conn.close()
