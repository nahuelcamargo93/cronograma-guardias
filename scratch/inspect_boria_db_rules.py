import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

print("--- Reglas individuales para BORIA MAYRA ---")
cursor.execute("SELECT * FROM personal_reglas WHERE personal_nombre = 'BORIA MAYRA'")
print(cursor.fetchall())

print("\n--- Ajustes individuales para BORIA MAYRA ---")
cursor.execute("SELECT * FROM personal_reglas_ajustes WHERE personal_nombre = 'BORIA MAYRA'")
print(cursor.fetchall())

conn.close()
