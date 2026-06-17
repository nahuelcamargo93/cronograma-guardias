import sqlite3
import json
from database.schema import inicializar_db

def main():
    print("Inicializando la base de datos para asegurar el catálogo de reglas...")
    inicializar_db()
    
    db_path = 'cronograma_inteligente.db'
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        
        # Parámetros para la nivelación de noches con inicio el 2026-07-01
        params = {
            "peso": 500,
            "nivelacion_historica": {
                "activo": True,
                "fecha_inicio": "2026-07-01",
                "tipo": "DESDE_FECHA"
            }
        }
        params_str = json.dumps(params)
        
        # Verificar si ya existe en servicios_reglas
        cur.execute("SELECT id FROM servicios_reglas WHERE servicio_id = 1 AND codigo_regla = 'PESO_BRECHA_TURNO'")
        row = cur.fetchone()
        if row:
            cur.execute("""
                UPDATE servicios_reglas 
                SET parametros_json = ?, activo = 1 
                WHERE servicio_id = 1 AND codigo_regla = 'PESO_BRECHA_TURNO'
            """, (params_str,))
            print("Regla PESO_BRECHA_TURNO actualizada para el Servicio 1.")
        else:
            cur.execute("""
                INSERT INTO servicios_reglas (servicio_id, codigo_regla, parametros_json, activo)
                VALUES (1, 'PESO_BRECHA_TURNO', ?, 1)
            """, (params_str,))
            print("Regla PESO_BRECHA_TURNO insertada y activada para el Servicio 1.")
        
        conn.commit()
        print("Configuración de la regla completada con éxito.")
    finally:
        conn.close()

if __name__ == '__main__':
    main()
