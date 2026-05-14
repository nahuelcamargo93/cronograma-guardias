import sqlite3

def set_demand():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    puesto_id = 9 # UTI (Service 2)
    
    # Weekday (Semana)
    semana_demand = [
        ('00:00', '06:00', 7),
        ('06:00', '12:00', 8),
        ('12:00', '18:00', 10),
        ('18:00', '00:00', 8)
    ]
    
    # Weekend/Holiday (Finde_Feriado)
    finde_demand = [
        ('00:00', '06:00', 6),
        ('06:00', '12:00', 7),
        ('12:00', '18:00', 9),
        ('18:00', '00:00', 7)
    ]
    
    # Clear existing demand for this puesto
    cursor.execute("DELETE FROM demanda_config WHERE puesto_id = ?;", (puesto_id,))
    
    # Insert new demand
    for start, end, qty in semana_demand:
        cursor.execute("""
            INSERT INTO demanda_config (puesto_id, tipo_dia, hora_inicio, hora_fin, cantidad, operador)
            VALUES (?, 'Semana', ?, ?, ?, '>=');
        """, (puesto_id, start, end, qty))
        
    for start, end, qty in finde_demand:
        cursor.execute("""
            INSERT INTO demanda_config (puesto_id, tipo_dia, hora_inicio, hora_fin, cantidad, operador)
            VALUES (?, 'Finde_Feriado', ?, ?, ?, '>=');
        """, (puesto_id, start, end, qty))
        
    conn.commit()
    print(f"Demand for puesto {puesto_id} set successfully.")
    conn.close()

if __name__ == "__main__":
    set_demand()
