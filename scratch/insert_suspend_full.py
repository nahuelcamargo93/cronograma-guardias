import sqlite3

def main():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    # Eliminar el ajuste anterior de la ultima semana para no tener duplicados raros
    cursor.execute("DELETE FROM servicios_reglas_ajustes WHERE servicio_id = 2 AND codigo_regla = 'ESQUEMA_SEMANAL_ENFERMERIA'")
    
    # Insertar la suspension para todo agosto
    query = """
    INSERT INTO servicios_reglas_ajustes 
    (servicio_id, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo) 
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    
    cursor.execute(query, (2, 'ESQUEMA_SEMANAL_ENFERMERIA', '2026-08-01', '2026-09-06', 'SUSPENDER', None, 1))
    conn.commit()
    conn.close()
    print("Ajuste de suspension total de ESQUEMA_SEMANAL_ENFERMERIA insertado correctamente.")

if __name__ == "__main__":
    main()
