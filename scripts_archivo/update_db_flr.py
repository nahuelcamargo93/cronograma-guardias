import sqlite3
import json

def update_flr_rules():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    # 1. Asegurar catálogo de reglas con tipos correctos
    # Ambas deben ser del tipo 'HARD'
    cursor.execute("""
        INSERT INTO reglas_catalogo (codigo_regla, tipo, descripcion)
        VALUES ('FINDE_LARGO_REGLAMENTARIO', 'HARD', 'Un bloque de 4 dias libres (Sab-Mar) por mes obligatorio')
        ON CONFLICT(codigo_regla) DO UPDATE SET tipo = 'HARD'
    """)
    
    cursor.execute("""
        INSERT INTO reglas_catalogo (codigo_regla, tipo, descripcion)
        VALUES ('FINDE_LARGO_REGLAMENTARIO_ESTRICTO', 'HARD', 'Finde largo obligatorio que debe caer dentro del mes')
        ON CONFLICT(codigo_regla) DO UPDATE SET tipo = 'HARD'
    """)
    
    # 2. Configurar servicios_reglas para el Servicio ID 2
    # Suspender FINDE_LARGO_REGLAMENTARIO
    cursor.execute("""
        INSERT INTO servicios_reglas (servicio_id, codigo_regla, parametros_json, activo)
        VALUES (2, 'FINDE_LARGO_REGLAMENTARIO', '{"suspendida": true}', 0)
        ON CONFLICT(servicio_id, codigo_regla) DO UPDATE SET
            parametros_json = '{"suspendida": true}',
            activo = 0
    """)
    
    # Activar FINDE_LARGO_REGLAMENTARIO_ESTRICTO en modo HARD
    cursor.execute("""
        INSERT INTO servicios_reglas (servicio_id, codigo_regla, parametros_json, activo)
        VALUES (2, 'FINDE_LARGO_REGLAMENTARIO_ESTRICTO', '{"suspendida": false, "cantidad": 1, "modo": "HARD"}', 1)
        ON CONFLICT(servicio_id, codigo_regla) DO UPDATE SET
            parametros_json = '{"suspendida": false, "cantidad": 1, "modo": "HARD"}',
            activo = 1
    """)
    
    conn.commit()
    conn.close()
    print("Reglas actualizadas correctamente en la base de datos (FINDE_LARGO_REGLAMENTARIO_ESTRICTO configurada como HARD para el servicio 2).")

if __name__ == "__main__":
    update_flr_rules()
