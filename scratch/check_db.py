import sqlite3

def check_db():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    for table in ['turnos_config', 'demanda_config']:
        print(f"\nSchema for {table}:")
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        for col in columns:
            print(col)
            
        print(f"\nData for {table} (Service 2):")
        cursor.execute(f"SELECT * FROM {table} WHERE servicio_id = 2")
        rows = cursor.fetchall()
        for r in rows:
            print(r)
    conn.close()

if __name__ == "__main__":
    check_db()
