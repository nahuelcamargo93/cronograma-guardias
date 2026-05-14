import sqlite3

def check_all_rules():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    print("Organizaciones Reglas:")
    cursor.execute("SELECT * FROM organizaciones_reglas;")
    for row in cursor.fetchall():
        print(f"  {row}")
        
    print("\nServicios Reglas:")
    cursor.execute("SELECT * FROM servicios_reglas;")
    for row in cursor.fetchall():
        print(f"  {row}")
        
    print("\nPersonal Reglas:")
    cursor.execute("SELECT * FROM personal_reglas;")
    for row in cursor.fetchall():
        print(f"  {row}")
        
    conn.close()

if __name__ == "__main__":
    check_all_rules()
