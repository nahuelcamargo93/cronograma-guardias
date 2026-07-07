import sqlite3
import json
import sys
import os

# Agregar directorio actual al path
sys.path.append(os.getcwd())

from database.connection import get_connection

def migrar_roles_servicio_1():
    servicio_id = 1
    
    # 1. Mapeo de personal a sus nuevos roles
    roles_map = {
        'Garcia, Luciano': 'Jefe',
        'Franco, Leandro': 'Coordinador UTI',
        'Moyano, Fernando': 'Coordinador UTI',
        'Toledo, Andrea': 'Coordinador UCO',
        'Camargo, Nahuel': 'Data / Kine',
        'Giacoppo, Veronica': 'Docencia / Kine',
        'Coniglio, Melisa': 'Materiales / Kine'
    }
    
    # 2. Empleados de los cuales copiaremos las reglas para definir el perfil del rol
    # (Para Coordinador UTI usamos Franco, Leandro como referencia)
    referencia_reglas_rol = {
        'Jefe': 'Garcia, Luciano',
        'Coordinador UTI': 'Franco, Leandro',
        'Coordinador UCO': 'Toledo, Andrea',
        'Data / Kine': 'Camargo, Nahuel',
        'Docencia / Kine': 'Giacoppo, Veronica',
        'Materiales / Kine': 'Coniglio, Melisa'
    }

    with get_connection() as conn:
        print("Iniciando migración atómica...")
        
        # A. Actualizar roles en la tabla personal
        for nombre, nuevo_rol in roles_map.items():
            conn.execute("""
                UPDATE personal 
                SET rol = ? 
                WHERE nombre = ? AND servicio_id = ?
            """, (nuevo_rol, nombre, servicio_id))
            print(f"Actualizado rol en personal: {nombre} -> {nuevo_rol}")

        # B. Copiar configuraciones de reglas personales a reglas de rol
        for rol, nombre_ref in referencia_reglas_rol.items():
            # Obtener las reglas activas de la persona de referencia
            reglas_ref = conn.execute("""
                SELECT codigo_regla, parametros_json 
                FROM personal_reglas 
                WHERE personal_nombre = ? AND activo = 1
            """, (nombre_ref,)).fetchall()
            
            for cod, params in reglas_ref:
                # Insertar o reemplazar en roles_reglas
                conn.execute("""
                    INSERT OR REPLACE INTO roles_reglas (servicio_id, rol, codigo_regla, parametros_json, activo)
                    VALUES (?, ?, ?, ?, 1)
                """, (servicio_id, rol, cod, params))
                print(f"Copiada regla al rol {rol}: {cod}")

        # C. Borrar las reglas personales de los empleados migrados
        # de modo que hereden limpiamente las reglas desde sus respectivos roles.
        for nombre in roles_map.keys():
            conn.execute("""
                DELETE FROM personal_reglas 
                WHERE personal_nombre = ?
            """, (nombre,))
            print(f"Limpiadas reglas individuales de: {nombre} (ahora heredará de su rol)")
            
        print("¡Migración y configuración completadas exitosamente!")

if __name__ == "__main__":
    migrar_roles_servicio_1()
