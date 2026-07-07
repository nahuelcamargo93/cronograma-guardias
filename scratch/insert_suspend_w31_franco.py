import sqlite3

def main():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    # 1. Eliminar cualquier ajuste anterior de MIN_FRANCOS_SEMANA en la semana 31 para el servicio 2
    cursor.execute("""
        DELETE FROM servicios_reglas_ajustes 
        WHERE servicio_id = 2 
          AND codigo_regla = 'MIN_FRANCOS_SEMANA' 
          AND fecha_inicio = '2026-07-27'
    """)
    
    # 2. Insertar la suspension para la semana 31 (27/7 al 2/8 de 2026)
    query = """
    INSERT INTO servicios_reglas_ajustes 
    (servicio_id, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo) 
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    cursor.execute(query, (2, 'MIN_FRANCOS_SEMANA', '2026-07-27', '2026-08-02', 'SUSPENDER', None, 1))
    
    conn.commit()
    conn.close()
    print("Ajuste de suspension de MIN_FRANCOS_SEMANA para la semana 31 insertado correctamente.")

if __name__ == "__main__":
    main()
