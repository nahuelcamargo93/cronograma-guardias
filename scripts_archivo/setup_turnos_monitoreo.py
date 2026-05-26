import sqlite3

def setup_monitoreo():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    # 1. Buscar el servicio_id de 'Personal de Monitoreo'
    cursor.execute("SELECT id FROM servicios WHERE nombre = 'Personal de Monitoreo'")
    res = cursor.fetchone()
    if not res:
        print("[ERROR] Servicio 'Personal de Monitoreo' no encontrado.")
        return
    servicio_id = res[0]
    print(f"[OK] Servicio 'Personal de Monitoreo' encontrado con ID: {servicio_id}")
    
    # 2. Asegurar puesto 'Monitoreo' para el servicio
    cursor.execute("SELECT id FROM puestos WHERE nombre = 'Monitoreo' AND servicio_id = ?", (servicio_id,))
    res_puesto = cursor.fetchone()
    if not res_puesto:
        cursor.execute("INSERT INTO puestos (servicio_id, nombre) VALUES (?, 'Monitoreo')", (servicio_id,))
        puesto_id = cursor.lastrowid
        print(f"[OK] Puesto 'Monitoreo' creado con ID: {puesto_id}")
    else:
        puesto_id = res_puesto[0]
        print(f"[OK] Puesto 'Monitoreo' ya existe con ID: {puesto_id}")
        
    # 3. Configurar los turnos
    turnos = [
        ('00-06', '00:00', 6, '0,1,2,3,4,5,6', 1),
        ('06-12', '06:00', 6, '0,1,2,3,4,5,6', 2),
        ('12-18', '12:00', 6, '0,1,2,3,4,5,6', 3),
        ('18-24', '18:00', 6, '0,1,2,3,4,5,6', 4)
    ]
    
    for nombre, hora_inicio, horas, dias_semana, orden in turnos:
        # Intentar actualizar por si existe
        cursor.execute("""
            UPDATE turnos_config 
            SET hora_inicio = ?, horas = ?, dias_semana = ?, puesto_id = ?, orden = ?, activo = 1
            WHERE nombre = ? AND servicio_id = ?
        """, (hora_inicio, horas, dias_semana, puesto_id, orden, nombre, servicio_id))
        
        # Insertar si no existe
        cursor.execute("""
            INSERT OR IGNORE INTO turnos_config (servicio_id, nombre, hora_inicio, horas, dias_semana, puesto_id, orden, activo)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1)
        """, (servicio_id, nombre, hora_inicio, horas, dias_semana, puesto_id, orden))
        
        print(f"   - Turno '{nombre}' configurado (Hora: {hora_inicio}, Duracion: {horas}hs)")
        
    conn.commit()
    conn.close()
    print("[SUCCESS] Configuracion de turnos para el Personal de Monitoreo completada con exito.")

if __name__ == "__main__":
    setup_monitoreo()
