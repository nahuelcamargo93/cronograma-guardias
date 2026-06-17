import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

# Ver el esquema de la tabla de infracciones o ver qué tablas la representan
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print("Tablas relacionadas con infracciones:", [t for t in tables if "infrac" in t])

# Vamos a ver qué columnas tiene la tabla 'infracciones_debug' (o como se llame)
for t in tables:
    if "infrac" in t:
        cursor.execute(f"PRAGMA table_info({t})")
        print(f"Columnas de {t}:", [r[1] for r in cursor.fetchall()])
        cursor.execute(f"SELECT * FROM {t} WHERE cronograma_id = 261")
        print(f"Filas en {t} para crono 261:")
        for r in cursor.fetchall():
            print(r)

# Qué empleados no tienen FLR en el crono 261?
cursor.execute("SELECT DISTINCT nombre FROM guardias WHERE cronograma_id = 261")
crono_emp = [row[0] for row in cursor.fetchall()]

cursor.execute("SELECT nombre FROM flr_asignados WHERE cronograma_id = 261")
flr_emp = [row[0] for row in cursor.fetchall()]

sin_flr = [e for e in crono_emp if e not in flr_emp]
print(f"\nEmpleados SIN FLR en crono 261 (Total: {len(sin_flr)}):", sin_flr)

conn.close()
