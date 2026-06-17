import sqlite3
import os
import json

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cronograma_inteligente.db")

def main():
    print("Intentando conectar a la base de datos con timeout de 60 segundos...")
    conn = sqlite3.connect(DB_PATH, timeout=60.0)
    cursor = conn.cursor()
    
    try:
        # Usaremos el nombre exacto de la base de datos
        nombre_db = 'Garcia, Luciano'
        
        # 1. Consultar reglas actuales de Garcia, Luciano
        print(f"Reglas actuales de {nombre_db} en personal_reglas:")
        cursor.execute("SELECT id, codigo_regla, parametros_json, activo FROM personal_reglas WHERE personal_nombre = ?", (nombre_db,))
        reglas = cursor.fetchall()
        for r in reglas:
            print(f"ID: {r[0]}, Regla: {r[1]}, Activo: {r[3]}\nJSON: {r[2]}\n")

        # 2. Insertar o actualizar ASIGNACION_FIJA para Garcia, Luciano
        asig_fija_json = json.dumps([
            {"Dia": "Lunes", "Turno": "Mañana_UTI"},
            {"Dia": "Martes", "Turno": "Mañana_UTI"},
            {"Dia": "Miercoles", "Turno": "Mañana_UTI"},
            {"Dia": "Jueves", "Turno": "Mañana_UTI"},
            {"Dia": "Viernes", "Turno": "Mañana_UTI"}
        ], ensure_ascii=False)

        # Buscar si ya tiene ASIGNACION_FIJA
        fija_existente = [r for r in reglas if r[1] == 'ASIGNACION_FIJA']
        if fija_existente:
            regla_id = fija_existente[0][0]
            cursor.execute(
                "UPDATE personal_reglas SET parametros_json = ?, activo = 1 WHERE id = ?",
                (asig_fija_json, regla_id)
            )
            print(f"Regla ASIGNACION_FIJA (ID {regla_id}) actualizada para {nombre_db}.")
        else:
            cursor.execute(
                "INSERT INTO personal_reglas (personal_nombre, codigo_regla, parametros_json, activo) VALUES (?, ?, ?, 1)",
                (nombre_db, 'ASIGNACION_FIJA', asig_fija_json)
            )
            print(f"Regla ASIGNACION_FIJA insertada correctamente para {nombre_db}.")

        # 3. Desactivar la regla MIN_TURNOS de Garcia, Luciano para evitar conflictos en semanas con feriados
        min_turnos_existente = [r for r in reglas if r[1] == 'MIN_TURNOS']
        if min_turnos_existente:
            regla_id = min_turnos_existente[0][0]
            cursor.execute(
                "UPDATE personal_reglas SET activo = 0 WHERE id = ?",
                (regla_id,)
            )
            print(f"Regla MIN_TURNOS (ID {regla_id}) desactivada (activo = 0) para {nombre_db}.")

        # Limpiar cualquier registro antiguo con el nombre 'Lic. Garcia' si existiera
        cursor.execute("DELETE FROM personal_reglas WHERE personal_nombre = 'Lic. Garcia'")
        
        conn.commit()
        print("Actualizacion finalizada con exito.")
    except sqlite3.OperationalError as e:
        print(f"\nError operativo: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
