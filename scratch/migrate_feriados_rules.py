import sys
import os
sys.path.append(os.getcwd())

import sqlite3
import json
from database.schema import inicializar_db, inicializar_catalogo_reglas

def run_migration():
    print("Initializing database and rule catalog...")
    inicializar_db()
    inicializar_catalogo_reglas()
    
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    # 1. Deactivate PESO_EQUIDAD_FL3 for Servicio 2 (Enfermeria)
    print("Suspending PESO_EQUIDAD_FL3 for Servicio 2...")
    cursor.execute("""
        INSERT OR REPLACE INTO servicios_reglas (servicio_id, codigo_regla, parametros_json, activo)
        VALUES (2, 'PESO_EQUIDAD_FL3', '{"suspendida": true}', 1)
    """)
    
    # 2. Deactivate PESO_EQUIDAD_FL4 for Servicio 2
    print("Suspending PESO_EQUIDAD_FL4 for Servicio 2...")
    cursor.execute("""
        INSERT OR REPLACE INTO servicios_reglas (servicio_id, codigo_regla, parametros_json, activo)
        VALUES (2, 'PESO_EQUIDAD_FL4', '{"suspendida": true}', 1)
    """)
    
    # 3. Insert and activate PESO_EQUIDAD_FERIADOS for Servicio 2
    print("Activating PESO_EQUIDAD_FERIADOS for Servicio 2...")
    cursor.execute("""
        INSERT OR REPLACE INTO servicios_reglas (servicio_id, codigo_regla, parametros_json, activo)
        VALUES (2, 'PESO_EQUIDAD_FERIADOS', '{"peso": 500}', 1)
    """)
    
    conn.commit()
    conn.close()
    print("Migration completed successfully!")

if __name__ == "__main__":
    run_migration()
