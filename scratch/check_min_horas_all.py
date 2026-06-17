import sqlite3

db_path = r"c:\Users\asus\Desktop\Ryoko\cronograma_inteligente\cronograma_inteligente.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- Configuración de MIN_HORAS_MES_CALENDARIO en servicios_reglas ---")
cursor.execute("SELECT * FROM servicios_reglas WHERE codigo_regla = 'MIN_HORAS_MES_CALENDARIO'")
for r in cursor.fetchall():
    print(r)

conn.close()
