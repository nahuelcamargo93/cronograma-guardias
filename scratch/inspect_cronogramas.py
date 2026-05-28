import sqlite3

db_path = "cronograma_inteligente.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Find last cronograma
cur.execute("SELECT id FROM cronogramas ORDER BY id DESC LIMIT 1")
last_cronograma_id = cur.fetchone()[0]
print(f"Last cronograma ID: {last_cronograma_id}")

print("\n--- GUARDIAS DE MATRICADI (con o sin r) EN EL ULTIMO CRONOGRAMA ---")
cur.execute("""
    SELECT fecha, turno, nombre
    FROM guardias
    WHERE cronograma_id = ? AND (nombre LIKE '%Matricardi%' OR nombre LIKE '%Matricadi%')
    ORDER BY fecha
""", (last_cronograma_id,))
for row in cur.fetchall():
    print(row)

print("\n--- TODOS LOS FRIDAY SHIFTS EN EL ULTIMO CRONOGRAMA (Servicio 3) ---")
# Let's get the list of personal in service 3
cur.execute("SELECT nombre FROM personal WHERE servicio_id = 3")
personal_3 = [r[0] for r in cur.fetchall()]

# Filter guardias that are Fridays (weekday 4). June 2026 Fridays are: June 5, 12, 19, 26.
# Let's count how many Fridays each person in service 3 has.
friday_counts = {}
cur.execute("""
    SELECT nombre, fecha, turno
    FROM guardias
    WHERE cronograma_id = ?
    ORDER BY nombre, fecha
""", (last_cronograma_id,))
for nombre, fecha, turno in cur.fetchall():
    if nombre in personal_3:
        # Check if Friday
        import datetime
        dt = datetime.date.fromisoformat(fecha)
        if dt.weekday() == 4: # Friday
            friday_counts[nombre] = friday_counts.get(nombre, []) + [fecha]

print("\nFridays worked by each employee in Service 3:")
for emp, dates in sorted(friday_counts.items(), key=lambda x: len(x[1]), reverse=True):
    print(f"  {emp}: {len(dates)} Fridays {dates}")

conn.close()
