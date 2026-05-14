import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

print("--- REGLAS DEL SERVICIO 2 ---")
cursor.execute("""
    SELECT c.codigo_regla, s.parametros_json 
    FROM servicios_reglas s 
    JOIN reglas_catalogo c ON s.regla_id = c.id 
    WHERE s.servicio_id = 2
""")
for row in cursor.fetchall():
    print(f"{row[0]}: {row[1]}")

print("\n--- REGLAS PERSONALES (TODAS) ---")
cursor.execute("""
    SELECT p.Nombre, c.codigo_regla, pr.parametros_json 
    FROM personal_reglas pr 
    JOIN reglas_catalogo c ON pr.regla_id = c.id 
    JOIN personal p ON pr.personal_id = p.id
""")
for row in cursor.fetchall():
    print(f"{row[0]} | {row[1]}: {row[2]}")

conn.close()
