import sqlite3
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import get_connection

def activate():
    conn = get_connection()
    # Check if the rule exists for service 4
    row = conn.execute("""
        SELECT id, activo, parametros_json 
        FROM servicios_reglas 
        WHERE servicio_id = 4 AND codigo_regla = 'PESO_EQUIDAD_FINDES_MENSUAL'
    """).fetchone()
    
    if row:
        rule_id, active, params = row
        print(f"Current State: Rule exists, Active={active}, Params={params}")
        conn.execute("""
            UPDATE servicios_reglas 
            SET activo = 1 
            WHERE servicio_id = 4 AND codigo_regla = 'PESO_EQUIDAD_FINDES_MENSUAL'
        """)
        conn.commit()
        print("SUCCESS: PESO_EQUIDAD_FINDES_MENSUAL activated in the database for Servicio 4.")
    else:
        # If it doesn't exist, insert it
        conn.execute("""
            INSERT INTO servicios_reglas (servicio_id, codigo_regla, parametros_json, activo)
            VALUES (4, 'PESO_EQUIDAD_FINDES_MENSUAL', '{"peso": 5000}', 1)
        """)
        conn.commit()
        print("SUCCESS: PESO_EQUIDAD_FINDES_MENSUAL created and activated in the database for Servicio 4.")

if __name__ == "__main__":
    activate()
