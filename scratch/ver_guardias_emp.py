import sqlite3
from datetime import date, timedelta

DB_PATH = "c:/Users/asus/Desktop/Ryoko/cronograma_inteligente/cronograma_inteligente.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 1. Consultar guardias de Abelenda Grisell en Cronograma 322
print("=== Guardias de ABELENDA GRISELL en Cronograma 322 ===")
rows = cursor.execute("""
    SELECT fecha, turno, horas 
    FROM guardias 
    WHERE cronograma_id = 322 AND nombre = 'ABELENDA GRISELL'
    ORDER BY fecha
""").fetchall()
for r in rows:
    print(f"Fecha: {r[0]}, Turno: {r[1]}, Horas: {r[2]}")

# 2. Consultar licencias de Abelenda Grisell en Julio 2026
print("\n=== Licencias de ABELENDA GRISELL ===")
lics = cursor.execute("""
    SELECT tipo, fecha_inicio, fecha_fin 
    FROM licencias 
    WHERE nombre = 'ABELENDA GRISELL' 
      AND (fecha_inicio <= '2026-07-31' AND fecha_fin >= '2026-07-01')
""").fetchall()
if lics:
    for l in lics:
        print(f"Tipo: {l[0]}, Inicio: {l[1]}, Fin: {l[2]}")
else:
    print("No tiene licencias registradas en Julio.")

# 3. Consultar semanas categorías de Abelenda Grisell en Cronograma 322
print("\n=== Categorías Semanales ===")
cats = cursor.execute("""
    SELECT fecha_lunes, categoria 
    FROM semanas_categorias 
    WHERE cronograma_id = 322 AND nombre = 'ABELENDA GRISELL'
    ORDER BY fecha_lunes
""").fetchall()
for c in cats:
    print(f"Lunes: {c[0]}, Categoría: {c[1]}")

conn.close()
