import sqlite3
import datetime

db_path = "cronograma_inteligente.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Get all personal for service 3
cur.execute("SELECT nombre FROM personal WHERE servicio_id = 3 AND activo = 1")
personal_3 = [r[0] for r in cur.fetchall()]

# Filter guardias that are Fridays (weekday 4). June 2026 Fridays are: June 5, 12, 19, 26.
# Let's count how many Fridays each person in service 3 has.
friday_counts = {}
cur.execute("""
    SELECT nombre, fecha, turno
    FROM guardias
    WHERE cronograma_id = 216
    ORDER BY nombre, fecha
""")
for nombre, fecha, turno in cur.fetchall():
    if nombre in personal_3:
        dt = datetime.date.fromisoformat(fecha)
        if dt.weekday() == 4: # Friday
            friday_counts[nombre] = friday_counts.get(nombre, []) + [fecha]

print("\nFridays worked by each employee in Service 3 for Cronograma ID 216:")
for emp, dates in sorted(friday_counts.items(), key=lambda x: len(x[1]), reverse=True):
    print(f"  {emp}: {len(dates)} Fridays {dates}")

conn.close()
