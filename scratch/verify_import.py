import sqlite3

def main():
    conn = sqlite3.connect('cronograma_inteligente.db')
    
    print('=== Checking New Personnel ===')
    cursor = conn.execute("SELECT nombre, rol, servicio_id FROM personal WHERE nombre IN ('ESCUDERO YANET', 'LUCERO SABRINA')")
    for row in cursor.fetchall():
        print(row)
        
    print('\n=== Checking Cronogramas ===')
    cursor = conn.execute("SELECT id, fecha_inicio, fecha_fin, estado, notas FROM cronogramas WHERE id >= 123 ORDER BY id")
    for row in cursor.fetchall():
        print(row)
        
    print('\n=== Checking Guardias counts per Cronograma ===')
    cursor = conn.execute("SELECT cronograma_id, COUNT(*) FROM guardias WHERE cronograma_id >= 123 GROUP BY cronograma_id ORDER BY cronograma_id")
    for row in cursor.fetchall():
        print(row)
        
    print('\n=== Checking Inactivated Turno ===')
    cursor = conn.execute("SELECT nombre, activo FROM turnos_config WHERE servicio_id = 2 AND nombre = 'TNN'")
    for row in cursor.fetchall():
        print(row)
        
    print('\n=== Checking Licencias counts for Service 2 ===')
    cursor = conn.execute("SELECT tipo, COUNT(*) FROM licencias l JOIN personal p ON l.nombre = p.nombre WHERE p.servicio_id = 2 GROUP BY tipo")
    for row in cursor.fetchall():
        print(row)
        
    print('\n=== Checking if any service 2 guardias remain in ID 92 ===')
    cursor = conn.execute("SELECT COUNT(*) FROM guardias WHERE cronograma_id = 92")
    print("Guardias in cronograma 92:", cursor.fetchone()[0])
    
    conn.close()

if __name__ == '__main__':
    main()
