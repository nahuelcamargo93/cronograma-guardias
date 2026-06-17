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
        
        # 1. Configurar PESO_EQUIDAD_FSL para servicio_id = 1
        params = {
            "peso_fl3": 500,
            "peso_fl4": 500,
            "nivelacion_historica": {
                "activo": True,
                "fecha_inicio": "2026-01-01",
                "tipo": "ANUAL"
            }
        }
        params_str = json.dumps(params)
        
        # Verificar si ya existe
        cur.execute("SELECT id FROM servicios_reglas WHERE servicio_id = 1 AND codigo_regla = 'PESO_EQUIDAD_FSL'")
        row = cur.fetchone()
        if row:
            cur.execute("""
                UPDATE servicios_reglas 
                SET parametros_json = ?, activo = 1 
                WHERE servicio_id = 1 AND codigo_regla = 'PESO_EQUIDAD_FSL'
            """, (params_str,))
            print("Regla PESO_EQUIDAD_FSL actualizada para el Servicio 1.")
        else:
            cur.execute("""
                INSERT INTO servicios_reglas (servicio_id, codigo_regla, parametros_json, activo)
                VALUES (1, 'PESO_EQUIDAD_FSL', ?, 1)
            """, (params_str,))
            print("Regla PESO_EQUIDAD_FSL insertada y activada para el Servicio 1.")
            
        # 2. Desactivar PESO_EQUIDAD_FL3 y PESO_EQUIDAD_FL4 para el Servicio 1
        cur.execute("""
            UPDATE servicios_reglas 
            SET activo = 0 
            WHERE servicio_id = 1 AND codigo_regla IN ('PESO_EQUIDAD_FL3', 'PESO_EQUIDAD_FL4')
        """)
        print("Reglas legacy PESO_EQUIDAD_FL3 y PESO_EQUIDAD_FL4 desactivadas para el Servicio 1.")
        
        conn.commit()
        print("Configuración completada con éxito.")
    finally:
        conn.close()

if __name__ == '__main__':
    main()
