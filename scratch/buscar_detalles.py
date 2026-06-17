import sqlite3

conn = sqlite3.connect("cronograma_inteligente.db")
cursor = conn.cursor()

print("--- Searching for ALCARAZ ---")
cursor.execute("SELECT nombre, servicio_id FROM personal WHERE nombre LIKE '%ALCARAZ%'")
for r in cursor.fetchall():
    print(r)

print("--- Searching for FRANCISCO ---")
cursor.execute("SELECT nombre, servicio_id FROM personal WHERE nombre LIKE '%FRANCISCO%'")
for r in cursor.fetchall():
    print(r)

print("--- Searching for GUIÑAZU ---")
cursor.execute("SELECT nombre, servicio_id FROM personal WHERE nombre LIKE '%GUI%'")
for r in cursor.fetchall():
    print(repr(r[0]), r[1])

conn.close()
