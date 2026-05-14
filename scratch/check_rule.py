import sqlite3

def check_service_rule():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    # Check if rule 2 exists for service 2
    cursor.execute("SELECT * FROM servicios_reglas WHERE servicio_id = 2 AND regla_id = 2;")
    row = cursor.fetchone()
    
    if row:
        print(f"Current rule for Enfermeria UTI: {row}")
    else:
        print("Rule DESC_POST_NOCHE not found for Enfermeria UTI.")
        # Check all rules for service 2 just in case
        cursor.execute("SELECT sr.*, rc.nombre FROM servicios_reglas sr JOIN reglas_catalogo rc ON sr.regla_id = rc.id WHERE sr.servicio_id = 2;")
        all_rules = cursor.fetchall()
        print("\nAll rules for Enfermeria UTI:")
        for r in all_rules:
            print(f"  {r}")
            
    conn.close()

if __name__ == "__main__":
    check_service_rule()
