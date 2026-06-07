import sqlite3

conn = sqlite3.connect("cronograma_inteligente.db")
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("TABLAS:")
for table in tables:
    print("-", table[0])

print("\nEstructura de la tabla de asignaciones o cronograma:")
# Busquemos si hay tablas que suenen a cronograma o asignaciones
for table in tables:
    name = table[0]
    if "cronograma" in name or "asignacion" in name or "resultado" in name or "turno" in name or "personal" in name:
        cursor.execute(f"PRAGMA table_info({name});")
        info = cursor.fetchall()
        print(f"\nTabla: {name}")
        for col in info:
            print(f"  {col[1]} ({col[2]})")
conn.close()
