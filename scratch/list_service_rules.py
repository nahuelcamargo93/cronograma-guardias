import sqlite3

def check_service_rules():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT sr.id, rc.codigo_regla, sr.parametros_json 
        FROM servicios_reglas sr 
        JOIN reglas_catalogo rc ON sr.regla_id = rc.id 
        WHERE sr.servicio_id = 2;
    """)
    rules = cursor.fetchall()
    print("Rules for Enfermeria UTI (ID 2):")
    for r in rules:
        print(f"  {r}")
        
    conn.close()

if __name__ == "__main__":
    check_service_rules()
