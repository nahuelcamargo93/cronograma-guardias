import os
import sys
import json

script_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else '.'
project_root = os.path.abspath(os.path.join(script_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from database.connection import get_connection

def insert_rule():
    servicio_id = 2
    codigo_regla = 'EXCLUIR_TURNOS'
    params = [{"turnos": ["TNN", "MT"], "dias": [5, 6]}]
    params_str = json.dumps(params)
    
    with get_connection() as conn:
        # Verificar si la regla existe para el servicio
        row = conn.execute("""
            SELECT id FROM servicios_reglas 
            WHERE servicio_id = ? AND codigo_regla = ?
        """, (servicio_id, codigo_regla)).fetchone()
        
        if row:
            print(f"Regla {codigo_regla} ya existe para servicio {servicio_id}. Actualizando...")
            conn.execute("""
                UPDATE servicios_reglas 
                SET parametros_json = ?, activo = 1 
                WHERE id = ?
            """, (params_str, row[0]))
        else:
            print(f"Insertando nueva regla {codigo_regla} para servicio {servicio_id}...")
            conn.execute("""
                INSERT INTO servicios_reglas (servicio_id, codigo_regla, parametros_json, activo)
                VALUES (?, ?, ?, 1)
            """, (servicio_id, codigo_regla, params_str))
        
        # Verificar el resultado
        res = conn.execute("""
            SELECT codigo_regla, parametros_json, activo 
            FROM servicios_reglas 
            WHERE servicio_id = ? AND codigo_regla = ?
        """, (servicio_id, codigo_regla)).fetchone()
        print(f"Resultado final en DB: Regla: {res[0]}, Activo: {res[2]}, Params: {res[1]}")

if __name__ == '__main__':
    insert_rule()
