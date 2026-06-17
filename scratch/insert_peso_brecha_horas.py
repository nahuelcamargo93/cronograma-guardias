import sqlite3

def run():
    conn = sqlite3.connect("cronograma_inteligente.db")
    cursor = conn.cursor()
    
    # 1. Asegurar catálogo de la regla
    cursor.execute("""
        INSERT OR IGNORE INTO reglas_catalogo (codigo_regla, tipo, descripcion)
        VALUES ('PESO_BRECHA_HORAS', 'SOFT', 'Peso de penalización por brecha incremental de horas asignadas en base a disponibilidad')
    """)
    
    # 2. Insertar / Actualizar en servicios_reglas para Servicio 1
    cursor.execute("""
        INSERT INTO servicios_reglas (servicio_id, codigo_regla, parametros_json, activo)
        VALUES (1, 'PESO_BRECHA_HORAS', '{"peso": 20, "fecha_inicio": "2026-06-22"}', 1)
        ON CONFLICT(servicio_id, codigo_regla) DO UPDATE SET
            parametros_json = excluded.parametros_json,
            activo = 1
    """)
    
    conn.commit()
    
    # Verificar
    cursor.execute("SELECT codigo_regla, parametros_json, activo FROM servicios_reglas WHERE servicio_id = 1 AND codigo_regla = 'PESO_BRECHA_HORAS'")
    row = cursor.fetchone()
    print("Regla en DB:", row)
    
    conn.close()

if __name__ == "__main__":
    run()
