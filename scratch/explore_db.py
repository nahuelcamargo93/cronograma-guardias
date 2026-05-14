import sqlite3

def get_db_info():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    # Get services
    cursor.execute("SELECT id, nombre FROM servicios;")
    services = cursor.fetchall()
    print(f"Services: {services}")
        
    # Get rules catalog
    cursor.execute("SELECT id, nombre, descripcion FROM reglas_catalogo;")
    catalog = cursor.fetchall()
    print("Rules Catalog:")
    for row in catalog:
        print(f"  {row}")
        
    # Get service rules for Enfermeria UTI (id=2)
    cursor.execute("""
        SELECT sr.id, rc.id as regla_id, rc.nombre, sr.valor, sr.activo 
        FROM servicios_reglas sr 
        JOIN reglas_catalogo rc ON sr.regla_id = rc.id 
        WHERE sr.servicio_id = 2;
    """)
    service_rules = cursor.fetchall()
    print("\nService Rules for Enfermeria UTI:")
    for row in service_rules:
        print(f"  {row}")
        
    conn.close()

if __name__ == "__main__":
    get_db_info()
