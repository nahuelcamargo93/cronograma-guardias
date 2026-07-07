import sqlite3

def check_db():
    conn = sqlite3.connect("cronograma_inteligente.db")
    cursor = conn.cursor()
    
    print("--- FRANCOS FORZADOS DE PALANA ---")
    rows = cursor.execute("""
        SELECT id, personal_nombre, fecha_inicio, fecha_fin, activo 
        FROM personal_francos_forzados 
        WHERE personal_nombre LIKE '%PALANA%'
    """).fetchall()
    
    # Obtener nombres de columnas
    colnames = [description[0] for description in cursor.description]
    print(colnames)
    for r in rows:
        print(r)
        
    print("\n--- REGLAS SERVICIO DE ENFERMERIA (SERVICIO 2) ---")
    rows_r = cursor.execute("""
        SELECT codigo_regla, activo, parametros_json 
        FROM servicios_reglas 
        WHERE servicio_id = 2
    """).fetchall()
    for r in rows_r:
        print(r)
        
    conn.close()

if __name__ == "__main__":
    check_db()
