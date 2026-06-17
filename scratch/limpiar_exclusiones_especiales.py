import sys
import os
import json

# Agregar el path del proyecto al path de python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_connection

def main():
    con = get_connection()
    try:
        cursor = con.cursor()
        
        # Profesionales a eliminar regla completa
        a_eliminar = [
            "Espinosa, Elizabeth",
            "Flores, Franco",
            "Guardia, Gabriel",
            "Guzman, Ariel",
            "Leonforte, Franco",
            "Marino, Emiliano",
            "Mesa, Bruno",
            "Sosa, Nicolas",
            "Syriani, Danae",
            "Vander, Nicolas",
            "Vivas, Eric",
            "Welch, Lucas"
        ]
        
        print("=== Eliminando exclusiones que solo contienen turnos especiales ===")
        for nombre in a_eliminar:
            cursor.execute("""
                DELETE FROM personal_reglas 
                WHERE personal_nombre = ? AND codigo_regla = 'EXCLUIR_TURNOS'
            """, (nombre,))
            print(f"- Eliminada regla EXCLUIR_TURNOS para: {nombre} (Filas afectadas: {cursor.rowcount})")
            
        # Profesionales a modificar json de exclusiones
        a_modificar = {
            "Garcia, Luciano": [
                {"turnos": ["Tarde_UTI", "Noche", "Mañana_UCO", "Tarde_UCO", "Dia_UCO"], "dias": [0, 1, 2, 3, 4, 5, 6]},
                {"turnos": ["Dia_UTI", "Dia_UCO"], "dias": [0, 1, 2, 3, 4]}
            ],
            "Franco, Leandro": [
                {"turnos": ["Tarde_UTI", "Mañana_UCO", "Tarde_UCO", "Dia_UCO", "Noche"], "dias": [0, 1, 2, 3, 4, 5, 6]},
                {"turnos": ["Dia_UTI", "Dia_UCO"], "dias": [0, 1, 2, 3, 4]}
            ],
            "Moyano, Fernando": [
                {"turnos": ["Mañana_UCO", "Tarde_UCO", "Dia_UCO", "Noche", "Tarde_UTI"], "dias": [0, 1, 2, 3, 4, 5, 6]},
                {"turnos": ["Dia_UTI", "Dia_UCO"], "dias": [0, 1, 2, 3, 4]}
            ],
            "Juarez, Eduardo": [
                {"turnos": ["Mañana_UTI", "Mañana_UCO", "Tarde_UTI", "Tarde_UCO"], "dias": [0, 1, 2, 3, 4, 5, 6]},
                {"turnos": ["Dia_UTI", "Dia_UCO"], "dias": [0, 1, 2, 3, 4]}
            ],
            "Camargo, Nahuel": [
                {"turnos": ["Mañana_UTI", "Mañana_UCO", "Dia_UTI", "Dia_UCO"], "dias": [0, 1, 2, 3, 4]},
                {"turnos": ["Noche"], "dias": [0, 1, 2, 3, 6]}
            ]
        }
        
        print("\n=== Actualizando exclusiones que contienen turnos comunes y especiales ===")
        for nombre, nuevo_json in a_modificar.items():
            nuevo_json_str = json.dumps(nuevo_json, ensure_ascii=False)
            cursor.execute("""
                UPDATE personal_reglas
                SET parametros_json = ?
                WHERE personal_nombre = ? AND codigo_regla = 'EXCLUIR_TURNOS'
            """, (nuevo_json_str, nombre))
            print(f"- Actualizada regla EXCLUIR_TURNOS para: {nombre} (Filas afectadas: {cursor.rowcount})")
            
        con.commit()
        print("\nCambios aplicados con éxito en la base de datos.")
    except Exception as e:
        con.rollback()
        print(f"Error al aplicar cambios: {e}")
    finally:
        con.close()

if __name__ == "__main__":
    main()
