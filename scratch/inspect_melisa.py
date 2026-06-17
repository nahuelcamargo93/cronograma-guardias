import sqlite3

db_path = r"c:\Users\asus\Desktop\Ryoko\cronograma_inteligente\cronograma_inteligente.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- Guardias de Coniglio, Melisa en cronograma 495 ---")
cursor.execute("SELECT * FROM guardias WHERE nombre = 'Coniglio, Melisa' AND cronograma_id = 495")
for r in cursor.fetchall():
    print(r)

print("\n--- Guardias de Coniglio, Melisa en cronograma 479 ---")
cursor.execute("SELECT * FROM guardias WHERE nombre = 'Coniglio, Melisa' AND cronograma_id = 479")
for r in cursor.fetchall():
    print(r)

print("\n--- Asignaciones fijas en la tabla personal_reglas para Melisa ---")
cursor.execute("SELECT * FROM personal_reglas WHERE personal_nombre = 'Coniglio, Melisa'")
for r in cursor.fetchall():
    print(r)

print("\n--- Asignaciones fijas en personal_reglas_ajustes para Melisa ---")
cursor.execute("SELECT * FROM personal_reglas_ajustes WHERE personal_nombre = 'Coniglio, Melisa'")
for r in cursor.fetchall():
    print(r)

conn.close()
