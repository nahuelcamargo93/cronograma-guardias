import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.connection import get_connection

def setup():
    print("Iniciando registro y asignación de la regla MAX_FRANCOS_CONTINUOS...")
    with get_connection() as conn:
        # 1. Registrar regla en el catálogo si no existe
        conn.execute("""
            INSERT OR IGNORE INTO reglas_catalogo (codigo_regla, tipo, descripcion)
            VALUES ('MAX_FRANCOS_CONTINUOS', 'HARD', 'Límite máximo de francos seguidos (consecutivos) permitidos. JSON: {"max_francos": 3, "modo": "HARD", "peso_soft": 10000}')
        """)
        print("- Regla MAX_FRANCOS_CONTINUOS registrada en el catálogo.")

        # 2. Configurar la regla para el servicio 2 (limitado a 3 francos consecutivos)
        conn.execute("""
            INSERT OR REPLACE INTO servicios_reglas (servicio_id, codigo_regla, parametros_json, activo)
            VALUES (2, 'MAX_FRANCOS_CONTINUOS', '{"max_francos": 3, "modo": "HARD", "peso_soft": 10000}', 1)
        """)
        print("- Regla activada en servicios_reglas para el servicio ID 2 (max_francos: 3, HARD).")

        # 3. Apagar la regla para POLETTI NATALIA en personal_reglas
        # Verificamos si existe POLETTI NATALIA en la tabla personal
        res = conn.execute("SELECT nombre FROM personal WHERE nombre = 'POLETTI NATALIA'").fetchone()
        if res:
            conn.execute("""
                INSERT OR REPLACE INTO personal_reglas (personal_nombre, codigo_regla, parametros_json, activo)
                VALUES ('POLETTI NATALIA', 'MAX_FRANCOS_CONTINUOS', '{"suspendida": true}', 1)
            """)
            print("- Regla desactivada (suspendida: true) en personal_reglas para 'POLETTI NATALIA'.")
        else:
            print("[ADVERTENCIA] No se encontró a 'POLETTI NATALIA' en la tabla personal.")

        conn.commit()
    print("Registro e inserción finalizados con éxito.")

if __name__ == "__main__":
    setup()
