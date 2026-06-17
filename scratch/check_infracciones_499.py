import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

print("=== Infracciones registradas para el Cronograma 499 ===")
cursor.execute("SELECT codigo_regla, detalle FROM infracciones_debug WHERE cronograma_id = 499")
rows = cursor.fetchall()
print(f"Total infracciones: {len(rows)}")

# Filtrar por las que no son penalizaciones soft típicas si las hay
for codigo, detalle in rows:
    # Mostremos todas para analizar
    print(f"Regla: {codigo} | Detalle: {detalle}")

conn.close()
