import sqlite3

def check_service_1_demand():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT dc.* 
        FROM demanda_config dc
        JOIN puestos p ON dc.puesto_id = p.id
        WHERE p.servicio_id = 1;
    """)
    for row in cursor.fetchall():
        print(row)
    conn.close()

if __name__ == "__main__":
    check_service_1_demand()
