import sqlite3

conn = sqlite3.connect("cronograma_inteligente.db")
cursor = conn.cursor()

names_to_check = [
    "ABELENDA",
    "ROJAS",
    "ESCUDERO",
    "ASTUDILLO",
    "BASCUR"
]

print("--- Matches in personal table ---")
for name in names_to_check:
    cursor.execute("SELECT nombre, rol, categoria, servicio_id FROM personal WHERE nombre LIKE ?", (f"%{name}%",))
    rows = cursor.fetchall()
    print(f"Query for '{name}':")
    if not rows:
        print("  NO MATCH")
    for row in rows:
        print(f"  Name: {row[0]}, Rol: {row[1]}, Cat: {row[2]}, Servicio_ID: {row[3]}")

conn.close()
