import sqlite3

def main():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    # 1. Eliminar cualquier ajuste anterior de ESQUEMA_SEMANAL_ENFERMERIA para el servicio 2
    cursor.execute("DELETE FROM servicios_reglas_ajustes WHERE servicio_id = 2 AND codigo_regla = 'ESQUEMA_SEMANAL_ENFERMERIA'")
    
    # 2. Insertar suspension para la Semana 31 (transicion de inicio de agosto)
    # del 27/7 al 2/8 de 2026
    query = """
    INSERT INTO servicios_reglas_ajustes 
    (servicio_id, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo) 
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    cursor.execute(query, (2, 'ESQUEMA_SEMANAL_ENFERMERIA', '2026-07-27', '2026-08-02', 'SUSPENDER', None, 1))
    
    # 3. Insertar suspension para la Semana 36 (transicion de fin de agosto)
    # del 31/8 al 6/9 de 2026
    cursor.execute(query, (2, 'ESQUEMA_SEMANAL_ENFERMERIA', '2026-08-31', '2026-09-06', 'SUSPENDER', None, 1))
    
    conn.commit()
    conn.close()
    print("Ajustes de suspension para las semanas de transicion (W31 y W36) insertados con exito.")

if __name__ == "__main__":
    main()
