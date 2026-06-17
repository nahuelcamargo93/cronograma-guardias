import sqlite3
conn = sqlite3.connect('cronograma.db')

# Buscar la tabla correcta
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print("Tablas:", [t[0] for t in tables])

# Buscar infracciones
for t in tables:
    name = t[0]
    if 'infra' in name.lower() or 'viola' in name.lower() or 'debug' in name.lower():
        print(f"\nTabla {name}:")
        cols = conn.execute(f"PRAGMA table_info({name})").fetchall()
        print("  Columnas:", [c[1] for c in cols])
        rows = conn.execute(f"SELECT * FROM {name} LIMIT 5").fetchall()
        for r in rows:
            print(f"  {r}")

conn.close()
