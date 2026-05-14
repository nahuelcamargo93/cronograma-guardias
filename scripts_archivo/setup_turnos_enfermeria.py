import sqlite3

def setup_turnos():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    # Verify IDs
    cursor.execute("SELECT id FROM servicios WHERE nombre = 'Enfermeria UTI'")
    res = cursor.fetchone()
    if not res:
        print("Service 'Enfermeria UTI' not found.")
        return
    servicio_id = res[0]
    
    cursor.execute("SELECT id FROM puestos WHERE nombre = 'UTI' AND servicio_id = ?", (servicio_id,))
    res = cursor.fetchone()
    if not res:
        print(f"Puesto 'UTI' not found for service {servicio_id}.")
        # Create it if it doesn't exist (though I should have created it before)
        cursor.execute("INSERT INTO puestos (servicio_id, nombre) VALUES (?, 'UTI')", (servicio_id,))
        puesto_id = cursor.lastrowid
        print(f"Created Puesto 'UTI' with ID {puesto_id}")
    else:
        puesto_id = res[0]
        
    print(f"Using Servicio ID: {servicio_id}, Puesto ID: {puesto_id}")
    
    turnos = [
        ('M', '06:00', 6, 1),
        ('T', '12:00', 6, 2),
        ('TN', '18:00', 6, 3),
        ('N', '00:00', 6, 4),
        ('TNN', '18:00', 12, 5)
    ]
    
    for nombre, inicio, horas, orden in turnos:
        cursor.execute("""
            INSERT INTO turnos_config (servicio_id, nombre, hora_inicio, horas, orden, activo, dias_semana, puesto_id)
            VALUES (?, ?, ?, ?, ?, 1, '0,1,2,3,4,5,6', ?)
        """, (servicio_id, nombre, inicio, horas, orden, puesto_id))
        
    conn.commit()
    print(f"Successfully added {len(turnos)} shifts for 'Enfermeria UTI'.")
    conn.close()

if __name__ == "__main__":
    setup_turnos()
