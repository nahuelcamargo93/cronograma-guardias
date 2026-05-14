import sqlite3

def add_mt_shift():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    # Check if MT already exists for service 2
    cursor.execute("SELECT id FROM turnos_config WHERE servicio_id = 2 AND nombre = 'MT' AND puesto_id = 9;")
    if cursor.fetchone():
        print("Shift MT already exists for service 2.")
    else:
        print("Adding shift MT for service 2...")
        cursor.execute("""
            INSERT INTO turnos_config (servicio_id, nombre, hora_inicio, horas, orden, activo, dias_semana, puesto_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (2, 'MT', '06:00', 12, 6, 1, '0,1,2,3,4,5,6', 9))
        conn.commit()
        print("Shift MT added successfully.")
        
    conn.close()

if __name__ == "__main__":
    add_mt_shift()
