import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.connection import get_connection

def configure():
    with get_connection() as conn:
        conn.execute("""
            UPDATE servicios_reglas 
            SET parametros_json = '{"max_francos": 3, "modo": "SOFT", "peso_soft": 10000}'
            WHERE servicio_id = 2 AND codigo_regla = 'MAX_FRANCOS_CONTINUOS'
        """)
        conn.commit()
    print("Regla MAX_FRANCOS_CONTINUOS configurada como SOFT para el servicio 2.")

if __name__ == "__main__":
    configure()
