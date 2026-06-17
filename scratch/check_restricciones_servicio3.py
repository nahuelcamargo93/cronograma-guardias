import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

print("=== Reglas de Servicio activas para Servicio 3 ===")
cursor.execute("SELECT codigo_regla, parametros_json FROM servicios_reglas WHERE servicio_id = 3 AND activo = 1")
for r in cursor.fetchall():
    print(f"Regla: {r[0]}")
    print(f"  Params: {r[1]}")

print("\n=== Reglas Personales activas para Personal del Servicio 3 ===")
cursor.execute("""
    SELECT pr.personal_nombre, pr.codigo_regla, pr.parametros_json 
    FROM personal_reglas pr
    JOIN personal p ON pr.personal_nombre = p.nombre
    WHERE p.servicio_id = 3 AND pr.activo = 1
""")
reglas_p = cursor.fetchall()
print(f"Total reglas personales: {len(reglas_p)}")
for r in reglas_p:
    print(f"Médico: {r[0]} | Regla: {r[1]}")
    print(f"  Params: {r[2]}")

conn.close()
