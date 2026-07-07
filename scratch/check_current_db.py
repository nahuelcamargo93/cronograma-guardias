import sqlite3

def main():
    conn = sqlite3.connect("cronograma_inteligente.db")
    cursor = conn.cursor()
    
    print("Estado actual de demanda_config para el puesto 32:")
    rows = cursor.execute("""
        SELECT id, puesto_id, tipo_dia, hora_inicio, hora_fin, cantidad_min, cantidad_max, dias_semana, activo 
        FROM demanda_config 
        WHERE puesto_id = 32
    """).fetchall()
    
    for r in rows:
        print(r)
        
    print("\nEstado actual de turnos_config para el puesto 32:")
    turnos = cursor.execute("""
        SELECT id, nombre, hora_inicio, horas, dias_semana, orden, activo 
        FROM turnos_config 
        WHERE puesto_id = 32
    """).fetchall()
    for t in turnos:
        print(t)
        
    conn.close()

if __name__ == "__main__":
    main()
