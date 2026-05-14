import sqlite3

def setup_simplified_demand():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    # IDs de puestos para Servicio 3
    # Planta: 10, Residente: 11
    
    # 1. Limpiar demanda actual del Servicio 3
    cursor.execute("DELETE FROM demanda_config WHERE puesto_id IN (10, 11)")
    
    # 2. Definir los dos bloques: 08-20 y 20-08
    # Definir bloques: (puesto_id, tipo_dia, hora_inicio, hora_fin, c_min, c_max)
    # Puesto 10: Planta, Puesto 11: Residente
    bloques = [
        # Planta (3 fijos)
        (10, 'Semana', '08:00', '20:00', 3, 3),
        (10, 'Semana', '20:00', '08:00', 3, 3),
        (10, 'Finde_Feriado', '08:00', '20:00', 3, 3),
        (10, 'Finde_Feriado', '20:00', '08:00', 3, 3),
        
        # Residente (1 fijo)
        (11, 'Semana', '08:00', '20:00', 1, 1),
        (11, 'Semana', '20:00', '08:00', 1, 1),
        (11, 'Finde_Feriado', '08:00', '20:00', 1, 1),
        (11, 'Finde_Feriado', '20:00', '08:00', 1, 1),
    ]
    
    for p_id, tipo, ini, fin, c_min, c_max in bloques:
        cursor.execute("""
            INSERT INTO demanda_config (puesto_id, tipo_dia, hora_inicio, hora_fin, cantidad_min, cantidad_max)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (p_id, tipo, ini, fin, c_min, c_max))
    
    conn.commit()
    conn.close()
    print("Simplified demand configuration (08-20 and 20-08) applied to Service 3.")

if __name__ == "__main__":
    setup_simplified_demand()
