import sqlite3
import os

os.chdir(r"c:\Users\asus\Desktop\Ryoko\cronograma_inteligente")
conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

# 1. Renombrar tabla vieja
cursor.execute("ALTER TABLE licencias RENAME TO licencias_old")

# 2. Crear tabla nueva
cursor.execute("""
    CREATE TABLE licencias (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre       TEXT NOT NULL REFERENCES personal(nombre),
        tipo         TEXT NOT NULL CHECK(tipo IN ('LPP', 'LAR', 'LM')),
        fecha_inicio TEXT NOT NULL,
        fecha_fin    TEXT NOT NULL
    )
""")

# 3. Migrar datos
cursor.execute("INSERT INTO licencias (id, nombre, tipo, fecha_inicio, fecha_fin) SELECT id, nombre, tipo, fecha_inicio, fecha_fin FROM licencias_old")

# 4. Eliminar vieja
cursor.execute("DROP TABLE licencias_old")

conn.commit()
print("Tabla licencias recreada con éxito.")
conn.close()
