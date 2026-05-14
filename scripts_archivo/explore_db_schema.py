import sqlite3

def get_db_info():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    tables = ['reglas_catalogo', 'servicios_reglas']
    for table in tables:
        print(f"\nSchema for {table}:")
        cursor.execute(f"PRAGMA table_info({table});")
        for col in cursor.fetchall():
            print(f"  {col}")
            
    # Also dump reglas_catalogo content
    cursor.execute("SELECT * FROM reglas_catalogo;")
    print("\nContent of reglas_catalogo:")
    for row in cursor.fetchall():
        print(f"  {row}")
        
    conn.close()

if __name__ == "__main__":
    get_db_info()
