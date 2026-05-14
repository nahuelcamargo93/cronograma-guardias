import sqlite3

def find_rule():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    # Get all rules to find the post-night rest one
    cursor.execute("SELECT * FROM reglas_catalogo;")
    rules = cursor.fetchall()
    print("Rules Catalog Search:")
    for row in rules:
        if any(term in str(row).lower() for term in ['descanso', 'post', 'noche', 'postnoche']):
            print(f"  {row}")
            
    conn.close()

if __name__ == "__main__":
    find_rule()
