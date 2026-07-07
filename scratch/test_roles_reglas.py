import sqlite3
import json
import sys
import os

# Agregar directorio actual al path
sys.path.append(os.getcwd())

from database.data_loader import obtener_empleados
from database.connection import get_connection

def run_test():
    servicio_id = 1
    # 1. Conectar a la base de datos
    with get_connection() as conn:
        # Limpiar cualquier residuo de prueba anterior
        conn.execute("DELETE FROM roles_reglas WHERE rol = 'Rotativo' AND codigo_regla = 'DESC_POST_NOCHE'")
        
        # Insertar una regla de prueba para el rol 'Rotativo'
        # Usar la regla DESC_POST_NOCHE
        params_json = json.dumps({"horas": 24})
        conn.execute("""
            INSERT INTO roles_reglas (servicio_id, rol, codigo_regla, parametros_json, activo)
            VALUES (?, ?, ?, ?, 1)
        """, (servicio_id, 'Rotativo', 'DESC_POST_NOCHE', params_json))
        print("Inserted test rule in roles_reglas for 'Rotativo'.")

    try:
        # 2. Cargar los empleados
        empleados = obtener_empleados(servicio_id, "2026-08-01", 31)
        
        # 3. Validar la fusión de reglas
        rotativos_con_regla = []
        jefes_con_regla = []
        
        for emp in empleados:
            if 'DESC_POST_NOCHE' in emp.reglas:
                if emp.rol == 'Rotativo':
                    rotativos_con_regla.append(emp.nombre)
                else:
                    jefes_con_regla.append(emp.nombre)
        
        print(f"\nRotativos que heredaron la regla del rol: {rotativos_con_regla}")
        print(f"No-Rotativos que heredaron la regla del rol (debería ser vacío): {jefes_con_regla}")
        
        # Aseveraciones
        assert len(rotativos_con_regla) > 0, "Error: Ningún rotativo heredó la regla."
        assert len(jefes_con_regla) == 0, f"Error: Empleados sin rol Rotativo heredaron la regla: {jefes_con_regla}"
        print("\n¡PRUEBA EXITOSA! La fusión de perfiles por rol funciona perfectamente.")
        
    finally:
        # 4. Limpiar la base de datos
        with get_connection() as conn:
            conn.execute("DELETE FROM roles_reglas WHERE rol = 'Rotativo' AND codigo_regla = 'DESC_POST_NOCHE'")
            print("Cleanup completed.")

if __name__ == "__main__":
    run_test()
