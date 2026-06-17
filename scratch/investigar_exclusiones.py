import sys
import os
import json

# Agregar el path del proyecto al path de python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_connection

def main():
    with get_connection() as conn:
        cursor = conn.cursor()
        
        print("=== SERVICIOS ===")
        cursor.execute("SELECT id, nombre FROM servicios")
        for row in cursor.fetchall():
            print(row)
            
        print("\n=== TURNOS CONFIG DEL SERVICIO 1 ===")
        cursor.execute("SELECT nombre, puesto_id, dias_semana, activo FROM turnos_config WHERE servicio_id = 1")
        for row in cursor.fetchall():
            print(row)
            
        print("\n=== PUESTOS DEL SERVICIO 1 ===")
        cursor.execute("SELECT id, nombre FROM puestos WHERE servicio_id = 1")
        for row in cursor.fetchall():
            print(row)
            
        print("\n=== REGLAS SERVICIO 1 ===")
        cursor.execute("SELECT codigo_regla, parametros_json, activo FROM servicios_reglas WHERE servicio_id = 1")
        for row in cursor.fetchall():
            print(row)
            
        print("\n=== REGLAS PERSONALES (EXCLUIR_TURNOS) DEL SERVICIO 1 ===")
        cursor.execute("""
            SELECT pr.personal_nombre, pr.codigo_regla, pr.parametros_json, pr.activo
            FROM personal_reglas pr
            JOIN personal p ON pr.personal_nombre = p.nombre
            WHERE p.servicio_id = 1 AND pr.codigo_regla = 'EXCLUIR_TURNOS'
        """)
        for row in cursor.fetchall():
            print(row)

if __name__ == "__main__":
    main()
