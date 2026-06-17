import os
import sys
import json

# Asegurar que la raíz del proyecto está en el PATH
script_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else '.'
project_root = os.path.abspath(os.path.join(script_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from database.schema import inicializar_db
from database.connection import get_connection

def main():
    print("Inicializando base de datos para asegurar el nuevo catálogo de reglas...")
    inicializar_db()

    servicio_id = 1
    codigo_regla = 'PUESTOS_SOLO_FIJOS'
    parametros = {"puestos": ["Especial"]}
    parametros_json = json.dumps(parametros)

    print(f"Activando regla {codigo_regla} para Servicio {servicio_id} con puestos {parametros['puestos']}...")
    
    with get_connection() as conn:
        # Asegurar inserción en catalogo por si acaso (inicializar_db ya lo hace)
        conn.execute("""
            INSERT OR IGNORE INTO reglas_catalogo (codigo_regla, tipo, descripcion)
            VALUES ('PUESTOS_SOLO_FIJOS', 'HARD', 'Puestos específicos donde las asignaciones son exclusivas a través de ASIGNACION_FIJA.')
        """)

        # Insertar o actualizar la regla en servicios_reglas
        conn.execute("""
            INSERT OR IGNORE INTO servicios_reglas (servicio_id, codigo_regla, activo, parametros_json)
            VALUES (?, ?, 1, ?)
        """, (servicio_id, codigo_regla, parametros_json))

        # Asegurar que quede activa y con los parámetros correctos
        conn.execute("""
            UPDATE servicios_reglas 
            SET activo = 1, parametros_json = ?
            WHERE servicio_id = ? AND codigo_regla = ?
        """, (parametros_json, servicio_id, codigo_regla))

        conn.commit()
        
        # Verificar estado
        row = conn.execute("""
            SELECT codigo_regla, activo, parametros_json 
            FROM servicios_reglas 
            WHERE servicio_id = ? AND codigo_regla = ?
        """, (servicio_id, codigo_regla)).fetchone()
        
        print("\nVerificación en DB:")
        if row:
            print(f"Regla: {row[0]} | Activo: {row[1]} | Parámetros: {row[2]}")
        else:
            print("Error: No se encontró la regla insertada.")

if __name__ == '__main__':
    main()
