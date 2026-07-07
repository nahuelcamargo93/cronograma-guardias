import os
import sys

# Asegurar que la raíz del proyecto está en el path para poder importar
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from database.connection import get_connection

def migrar():
    with get_connection() as conn:
        print("Insertando regla DISTANCIA_MINIMA_TIPO_SEMANA en reglas_catalogo...")
        conn.execute("""
            INSERT OR IGNORE INTO reglas_catalogo (codigo_regla, tipo, descripcion)
            VALUES (
                'DISTANCIA_MINIMA_TIPO_SEMANA', 
                'HARD', 
                'Asegura una distancia mínima en semanas entre semanas de una misma categoría de turno'
            )
        """)

        print("Configurando regla DISTANCIA_MINIMA_TIPO_SEMANA para el Servicio ID 2...")
        conn.execute("""
            INSERT OR REPLACE INTO servicios_reglas (servicio_id, codigo_regla, parametros_json, activo)
            VALUES (
                2, 
                'DISTANCIA_MINIMA_TIPO_SEMANA', 
                '{"modo": "HARD", "distancias": {"N": 3, "TN": 3}}', 
                1
            )
        """)

        print("Inactivando regla NO_REPETIR_N_CONSECUTIVO para el Servicio ID 2...")
        conn.execute("""
            UPDATE servicios_reglas 
            SET activo = 0 
            WHERE servicio_id = 2 AND codigo_regla = 'NO_REPETIR_N_CONSECUTIVO'
        """)

        print("Inactivando regla PENALIZACION_TURNO_AUSENTE para el Servicio ID 2...")
        conn.execute("""
            UPDATE servicios_reglas 
            SET activo = 0 
            WHERE servicio_id = 2 AND codigo_regla = 'PENALIZACION_TURNO_AUSENTE'
        """)

        conn.commit()
        print("[OK] Migración completada con éxito.")

if __name__ == "__main__":
    migrar()
