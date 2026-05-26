import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
cur = conn.cursor()

# Inspect columns of servicios_reglas
cur.execute("PRAGMA table_info(servicios_reglas)")
columns = cur.fetchall()
print("servicios_reglas columns:")
for col in columns:
    print(f"  {col[1]} ({col[2]})")

# Print current rows in servicios_reglas for service_id = 2
cur.execute("SELECT * FROM servicios_reglas WHERE servicio_id = 2")
rows = cur.fetchall()
print("\nRows in servicios_reglas for service_id = 2:")
for row in rows:
    print(f"  {row}")

conn.close()
