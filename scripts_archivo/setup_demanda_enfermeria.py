import sqlite3

def setup_demanda():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    # Verify Puesto ID for Enfermeria UTI
    cursor.execute("""
        SELECT p.id 
        FROM puestos p
        JOIN servicios s ON p.servicio_id = s.id
        WHERE s.nombre = 'Enfermeria UTI' AND p.nombre = 'UTI'
    """)
    res = cursor.fetchone()
    if not res:
        print("Puesto 'UTI' for 'Enfermeria UTI' not found.")
        return
    puesto_id = res[0]
    print(f"Using Puesto ID: {puesto_id}")
    
    # Demand configuration
    # (puesto_id, tipo_dia, hora_inicio, hora_fin, cantidad, operador)
    demandas = [
        (puesto_id, 'Semana', '00:00', '06:00', 6, '>='),
        (puesto_id, 'Semana', '06:00', '12:00', 9, '>='),
        (puesto_id, 'Semana', '12:00', '18:00', 8, '>='),
        (puesto_id, 'Semana', '18:00', '00:00', 7, '>='),
        (puesto_id, 'Finde_Feriado', '00:00', '06:00', 6, '>='),
        (puesto_id, 'Finde_Feriado', '06:00', '12:00', 9, '>='),
        (puesto_id, 'Finde_Feriado', '12:00', '18:00', 8, '>='),
        (puesto_id, 'Finde_Feriado', '18:00', '00:00', 7, '>='),
    ]
    
    # Clear existing demand for this puesto just in case
    cursor.execute("DELETE FROM demanda_config WHERE puesto_id = ?", (puesto_id,))
    
    for d in demandas:
        cursor.execute("""
            INSERT INTO demanda_config (puesto_id, tipo_dia, hora_inicio, hora_fin, cantidad, operador)
            VALUES (?, ?, ?, ?, ?, ?)
        """, d)
        
    conn.commit()
    print(f"Successfully added {len(demandas)} demand rules for Enfermeria UTI.")
    conn.close()

if __name__ == "__main__":
    setup_demanda()
