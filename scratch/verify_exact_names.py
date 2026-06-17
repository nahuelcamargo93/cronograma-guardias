import sqlite3

DB_PATH = "cronograma_inteligente.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

keys = ["Arias", "Baracat", "Mora", "Noriega", "Zeballos", "Pacheco", "Diaz", "Nesteruk", "Quiroga", "Sánchez", "Villegas"]

for k in keys:
    print(f"\nResultados para '{k}':")
    # Intentar buscar que empiece con el apellido o contenga el apellido como palabra
    cursor.execute("SELECT nombre FROM personal WHERE servicio_id = 3 AND (nombre LIKE ? OR nombre LIKE ?);", (f"{k}%", f"% {k}%"))
    rows = cursor.fetchall()
    for r in rows:
        print(f"  - {repr(r[0])}")

conn.close()
