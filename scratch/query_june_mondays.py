import sqlite3

DB_PATH = "cronograma_inteligente.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("--- GUARDIAS EN CRONOGRAMA 37 POR DIA ---")
cursor.execute("""
    SELECT fecha, nombre, turno, horas, es_finde
    FROM guardias
    WHERE cronograma_id = 37
    ORDER BY fecha, nombre;
""")
guardias = cursor.fetchall()
# Print grouped by date
current_date = None
for g in guardias:
    if g[0] != current_date:
        current_date = g[0]
        print(f"\nFecha: {current_date}")
    print(f"  {g[1]}: {g[2]} ({g[3]} hs, es_finde={g[4]})")

conn.close()
