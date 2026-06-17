import sqlite3
import os
import json

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cronograma_inteligente.db")

def main():
    print("Intentando conectar a la base de datos con timeout de 60 segundos...")
    conn = sqlite3.connect(DB_PATH, timeout=60.0)
    cursor = conn.cursor()
    
    try:
        nombre_db = 'Giacoppo, Veronica'
        
        # 1. Consultar reglas actuales de Giacoppo, Veronica
        print(f"Reglas actuales de {nombre_db} en personal_reglas:")
        cursor.execute("SELECT id, codigo_regla, parametros_json, activo FROM personal_reglas WHERE personal_nombre = ?", (nombre_db,))
        reglas = cursor.fetchall()
        for r in reglas:
            print(f"ID: {r[0]}, Regla: {r[1]}, Activo: {r[3]}\nJSON: {r[2]}\n")

        # 2. Insertar o actualizar PESO_INCONSISTENCIA para Giacoppo, Veronica
        peso_json = json.dumps({"peso": 1000}, ensure_ascii=False)

        # Buscar si ya tiene PESO_INCONSISTENCIA
        existente = [r for r in reglas if r[1] == 'PESO_INCONSISTENCIA']
        if existente:
            regla_id = existente[0][0]
            cursor.execute(
                "UPDATE personal_reglas SET parametros_json = ?, activo = 1 WHERE id = ?",
                (peso_json, regla_id)
            )
            print(f"Regla PESO_INCONSISTENCIA (ID {regla_id}) actualizada para {nombre_db}.")
        else:
            cursor.execute(
                "INSERT INTO personal_reglas (personal_nombre, codigo_regla, parametros_json, activo) VALUES (?, ?, ?, 1)",
                (nombre_db, 'PESO_INCONSISTENCIA', peso_json)
            )
            print(f"Regla PESO_INCONSISTENCIA insertada correctamente para {nombre_db}.")

        conn.commit()
        print("Actualizacion finalizada con exito.")
    except sqlite3.OperationalError as e:
        print(f"\nError operativo: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
