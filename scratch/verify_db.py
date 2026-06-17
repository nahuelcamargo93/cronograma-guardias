import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

coordinadores_y_jefe = ["Garcia, Luciano", "Toledo, Andrea", "Franco, Leandro", "Moyano, Fernando"]

print("=== Verificación de registros en la DB ===")
for nombre in coordinadores_y_jefe:
    cursor.execute("SELECT parametros_json FROM personal_reglas WHERE personal_nombre = ? AND codigo_regla = 'EXCLUIR_TURNOS'", (nombre,))
    row = cursor.fetchone()
    if row:
        # Imprimimos la representación cruda de la cadena almacenada para verificar la codificación
        print(f"Empleado: {nombre}")
        print(f"  Raw string in DB: {repr(row[0])}")
        try:
            parsed = json.loads(row[0])
            print(f"  Parsed JSON: {parsed}")
        except Exception as e:
            print(f"  Error al parsear: {e}")
            
conn.close()
