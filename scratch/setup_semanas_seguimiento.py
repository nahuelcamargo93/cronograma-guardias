import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.connection import get_connection
from database.schema import inicializar_db, inicializar_catalogo_reglas
import json

def setup():
    # 1. Asegurar esquema y catálogo actualizados
    print("Inicializando base de datos y cargando catálogo...")
    inicializar_db()
    inicializar_catalogo_reglas()
    
    # 2. Insertar regla para Lic. Giaccoppo
    nombre_profesional = "Lic. Giaccoppo"
    codigo_regla = "SEMANAS_SEGUIMIENTO_REQUERIDAS"
    parametros = {
        "min_manana": 1,
        "min_tarde": 2,
        "min_total": 3
    }
    parametros_json = json.dumps(parametros)
    
    with get_connection() as conn:
        # Verificar si ya existe
        cur = conn.execute("""
            SELECT id, parametros_json, activo 
            FROM personal_reglas 
            WHERE personal_nombre = ? AND codigo_regla = ?
        """, (nombre_profesional, codigo_regla))
        row = cur.fetchone()
        
        if row:
            print(f"La regla ya existe para {nombre_profesional}. Actualizando parámetros...")
            conn.execute("""
                UPDATE personal_reglas 
                SET parametros_json = ?, activo = 1 
                WHERE id = ?
            """, (parametros_json, row[0]))
        else:
            print(f"Creando registro de regla para {nombre_profesional}...")
            # Obtener el servicio de Lic. Giaccoppo
            cur_serv = conn.execute("SELECT servicio_id FROM personal WHERE nombre = ?", (nombre_profesional,))
            serv_row = cur_serv.fetchone()
            servicio_id = serv_row[0] if serv_row else 1
            
            conn.execute("""
                INSERT INTO personal_reglas (personal_nombre, codigo_regla, parametros_json, activo, servicio_id)
                VALUES (?, ?, ?, 1, ?)
            """, (nombre_profesional, codigo_regla, parametros_json, servicio_id))
            
        print("Regla configurada con éxito.")
        
        # Mostrar las reglas actuales de Lic. Giaccoppo
        print("\nReglas activas para Lic. Giaccoppo:")
        cur_rules = conn.execute("""
            SELECT codigo_regla, parametros_json, activo 
            FROM personal_reglas 
            WHERE personal_nombre = ?
        """, (nombre_profesional,))
        for r in cur_rules.fetchall():
            print(f" - {r[0]}: {r[1]} (Activo: {r[2]})")

if __name__ == "__main__":
    setup()
