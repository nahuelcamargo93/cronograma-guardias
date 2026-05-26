import sqlite3

def main():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    # Let's get all cronograma_id in guardias
    c_ids_all = [r[0] for r in cursor.execute("SELECT DISTINCT cronograma_id FROM guardias").fetchall()]
    print("All cronograma_ids in guardias:", sorted(c_ids_all))
    
    # Let's get all cronograma_id for service 3
    c_ids_s3 = [r[0] for r in cursor.execute("""
        SELECT DISTINCT g.cronograma_id 
        FROM guardias g
        JOIN personal p ON g.nombre = p.nombre
        WHERE p.servicio_id = 3
    """).fetchall()]
    print("Service 3 cronograma_ids in guardias:", sorted(c_ids_s3))
    
    conn.close()

if __name__ == '__main__':
    main()
