import sqlite3

def main():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    # 1. Eliminar cualquier ajuste anterior de ESQUEMA_SEMANAL_ENFERMERIA para el servicio 2
    cursor.execute("DELETE FROM servicios_reglas_ajustes WHERE servicio_id = 2 AND codigo_regla = 'ESQUEMA_SEMANAL_ENFERMERIA'")
    
    # 2. Insertar la suspension para todo agosto (1/8 al 31/8)
    query = """
    INSERT INTO servicios_reglas_ajustes 
    (servicio_id, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo) 
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    cursor.execute(query, (2, 'ESQUEMA_SEMANAL_ENFERMERIA', '2026-08-01', '2026-08-31', 'SUSPENDER', None, 1))
    
    conn.commit()
    conn.close()
    print("Ajuste de suspension total de ESQUEMA_SEMANAL_ENFERMERIA para agosto insertado.")

if __name__ == "__main__":
    main()
