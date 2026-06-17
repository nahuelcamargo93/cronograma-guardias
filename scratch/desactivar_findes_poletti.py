import sqlite3
import json

DB_PATH = "cronograma_inteligente.db"

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    regla_codigo = "MANEJO_FINDES"
    empleado = "POLETTI NATALIA"

    # Verificar si POLETTI NATALIA existe
    persona = cursor.execute("SELECT nombre, servicio_id FROM personal WHERE nombre = ?", (empleado,)).fetchone()
    if persona:
        nombre, servicio_id = persona
        cursor.execute("""
            INSERT INTO personal_reglas (personal_nombre, codigo_regla, parametros_json, activo)
            VALUES (?, ?, ?, 1)
            ON CONFLICT(personal_nombre, codigo_regla) 
            DO UPDATE SET parametros_json = excluded.parametros_json, activo = 1
        """, (nombre, regla_codigo, json.dumps({"suspendida": True})))
        print(f"Regla {regla_codigo} suspendida en personal_reglas para {nombre}.")
    else:
        print(f"Error: No se encontró al empleado {empleado}.")

    conn.commit()
    conn.close()

if __name__ == '__main__':
    main()
