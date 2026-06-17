import sqlite3

conn = sqlite3.connect("cronograma_inteligente.db")
cursor = conn.cursor()

names = [
    "ABELENDA GRISELL",
    "ROJAS JULIANA",
    "ESCUDERO SERGIO",
    "ASTUDILLO MELINA",
    "BASCUR ALEJANDRA"
]

print("--- Existing personal_reglas_ajustes for these names in July 2026 ---")
for name in names:
    cursor.execute("""
        SELECT id, personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, activo, servicio_id 
        FROM personal_reglas_ajustes 
        WHERE personal_nombre = ? AND (fecha_inicio LIKE '2026-07%' OR fecha_fin LIKE '2026-07%')
    """, (name,))
    rows = cursor.fetchall()
    print(f"Name: {name}")
    if not rows:
        print("  None")
    for row in rows:
        print(f"  {row}")

conn.close()
