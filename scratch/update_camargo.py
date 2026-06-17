import sqlite3
import json
import time

def main():
    # Aumentar timeout a 30 segundos en caso de que esté bloqueado temporariamente
    conn = sqlite3.connect('cronograma_inteligente.db', timeout=30.0)
    cursor = conn.cursor()
    
    try:
        # 1. Actualizar ASIGNACION_FIJA para Lic. Camargo N. (id = 22)
        nueva_asignacion = [
            {"Dia": "Lunes", "Turno": "Tarde_especial", "Tipo": "Especial", "Horas": 6},
            {"Dia": "Miercoles", "Turno": "Tarde_UTI", "Tipo": "Asistencial", "Horas": 6}
        ]
        cursor.execute(
            "UPDATE personal_reglas SET parametros_json = ? WHERE id = 22",
            (json.dumps(nueva_asignacion),)
        )
        
        # 2. Eliminar la preferencia de domingo (id = 119)
        cursor.execute("DELETE FROM personal_reglas WHERE id = 119")
        
        conn.commit()
        print("Cambios realizados con éxito.")
        
        # Mostrar estado actual de Camargo
        cursor.execute("SELECT id, codigo_regla, parametros_json FROM personal_reglas WHERE personal_nombre = 'Lic. Camargo N.'")
        for row in cursor.fetchall():
            print(row)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    main()
