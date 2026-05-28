import sqlite3
import datetime

db_path = "cronograma_inteligente.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Get all personal for service 3
cur.execute("SELECT nombre, rol FROM personal WHERE servicio_id = 3 AND activo = 1")
personal_list = cur.fetchall()
print(f"Total active personal in Service 3: {len(personal_list)}")
personal_names = [p[0] for p in personal_list]

# Let's count how many Friday shifts are assigned in cronograma 215
cur.execute("""
    SELECT fecha, turno, nombre
    FROM guardias
    WHERE cronograma_id = 215
    ORDER BY fecha, turno
""")
guardias = cur.fetchall()

# Fridays in June 2026: 5, 12, 19, 26
fridays = ["2026-06-05", "2026-06-12", "2026-06-19", "2026-06-26"]
guardias_fridays = [g for g in guardias if g[0] in fridays and g[2] in personal_names]

print(f"\nTotal guardias on Fridays in Cronograma 215 for Service 3: {len(guardias_fridays)}")
for g in guardias_fridays:
    print(f"  {g[0]} | {g[1]} | {g[2]}")

conn.close()
