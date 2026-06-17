import sqlite3

DB_PATH = "c:/Users/asus/Desktop/Ryoko/cronograma_inteligente/cronograma_inteligente.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("=== Guardias de ABELENDA GRISELL en Cronograma 324 (HARD 12h) ===")
rows = cursor.execute("""
    SELECT fecha, turno, horas 
    FROM guardias 
    WHERE cronograma_id = 324 AND nombre = 'ABELENDA GRISELL'
    ORDER BY fecha
""").fetchall()
for r in rows:
    print(f"Fecha: {r[0]}, Turno: {r[1]}, Horas: {r[2]}")

print("\n=== Categorías Semanales ===")
cats = cursor.execute("""
    SELECT fecha_lunes, categoria 
    FROM semanas_categorias 
    WHERE cronograma_id = 324 AND nombre = 'ABELENDA GRISELL'
    ORDER BY fecha_lunes
""").fetchall()
for c in cats:
    print(f"Lunes: {c[0]}, Categoría: {c[1]}")

conn.close()
