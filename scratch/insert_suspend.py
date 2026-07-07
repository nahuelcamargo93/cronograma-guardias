import sqlite3

def main():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    # Insertar el ajuste
    query = """
    INSERT INTO servicios_reglas_ajustes 
    (servicio_id, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo) 
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    
    cursor.execute(query, (2, 'ESQUEMA_SEMANAL_ENFERMERIA', '2026-08-31', '2026-09-06', 'SUSPENDER', None, 1))
    conn.commit()
    conn.close()
    print("Ajuste insertado correctamente en la base de datos.")

if __name__ == "__main__":
    main()
