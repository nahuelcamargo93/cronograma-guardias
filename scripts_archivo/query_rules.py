import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

print("--- REGLAS PERSONALES ---")
cursor.execute("""
    SELECT personal_nombre, rc.codigo_regla, parametros_json 
    FROM personal_reglas pr 
    JOIN reglas_catalogo rc ON pr.regla_id = rc.id;
""")
for row in cursor.fetchall():
    print(f"Persona: {row[0]} | Regla: {row[1]} | Params: {row[2]}")

print("\n--- ASIGNACIONES FIJAS (REGLAS PERSONALES) ---")
# Buscamos en el JSON de reglas personales si hay asignaciones fijas
# Nota: ASIGNACION_FIJA es un código de regla en el catálogo.

cursor.execute("""
    SELECT personal_nombre, parametros_json 
    FROM personal_reglas pr 
    JOIN reglas_catalogo rc ON pr.regla_id = rc.id
    WHERE rc.codigo_regla = 'ASIGNACION_FIJA';
""")
for row in cursor.fetchall():
    print(f"Persona: {row[0]} | Asignación: {row[1]}")

conn.close()
