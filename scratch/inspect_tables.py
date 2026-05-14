import sqlite3

def inspect_tables():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    tables = ['organizaciones', 'servicios', 'personal', 'puestos']
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table});")
        print(f"Table: {table}")
        for col in cursor.fetchall():
            print(f"  - {col}")
    
    print("\nCurrent Organizations:")
    cursor.execute("SELECT * FROM organizaciones")
    for row in cursor.fetchall():
        print(f"  - {row}")
        
    print("\nCurrent Services:")
    cursor.execute("SELECT * FROM servicios")
    for row in cursor.fetchall():
        print(f"  - {row}")

    conn.close()

if __name__ == "__main__":
    inspect_tables()
