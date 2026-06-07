import sqlite3

conn = sqlite3.connect("cronograma_inteligente.db")
cursor = conn.cursor()

for table in ["guardias", "feriados", "feriados_exclusiones"]:
    cursor.execute(f"PRAGMA table_info({table});")
    info = cursor.fetchall()
    print(f"\nTabla: {table}")
    for col in info:
        print(f"  {col[1]} ({col[2]})")

cursor.execute("SELECT * FROM feriados LIMIT 20;")
print("\nEjemplos de feriados:")
for r in cursor.fetchall():
    print(r)

cursor.execute("SELECT * FROM guardias LIMIT 5;")
print("\nEjemplos de guardias:")
for r in cursor.fetchall():
    print(r)

conn.close()
