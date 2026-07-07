import sqlite3
import json
import os

def main():
    db_path = 'cronograma_inteligente.db'
    if not os.path.exists(db_path):
        print(f"Error: No se encontró la base de datos en {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("=== Migración de Regla TURNO_PREVIO_LICENCIA ===")
    
    # 1. Insertar en reglas_catalogo
    cursor.execute("""
        INSERT OR IGNORE INTO reglas_catalogo (codigo_regla, tipo, descripcion)
        VALUES ('TURNO_PREVIO_LICENCIA', 'HARD', 'Prohíbe un tipo de turno el día previo al inicio de una licencia.')
    """)
    print("Regla inyectada en el catálogo si no existía.")

    # 2. Insertar/Actualizar en servicios_reglas para servicio_id = 2
    params = {"turnos": ["N"]}
    params_str = json.dumps(params)
    
    cursor.execute("""
        INSERT OR IGNORE INTO servicios_reglas (servicio_id, codigo_regla, parametros_json, activo)
        VALUES (2, 'TURNO_PREVIO_LICENCIA', ?, 1)
    """, (params_str,))
    
    cursor.execute("""
        UPDATE servicios_reglas
        SET parametros_json = ?, activo = 1
        WHERE servicio_id = 2 AND codigo_regla = 'TURNO_PREVIO_LICENCIA'
    """, (params_str,))
    
    print("Regla activada para el servicio 2 (Enfermería) prohibiendo turno Noche (N).")

    conn.commit()
    conn.close()
    print("Migración completada con éxito.")

if __name__ == "__main__":
    main()
