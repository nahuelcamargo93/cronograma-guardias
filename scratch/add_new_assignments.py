import sqlite3

def main():
    conn = sqlite3.connect('cronograma_inteligente.db', timeout=30.0)
    cursor = conn.cursor()
    
    print("=== INSERTANDO NUEVAS ASIGNACIONES (CRONO 152) ===")
    
    try:
        # Godoy Maria
        cursor.execute("""
            INSERT INTO guardias (cronograma_id, nombre, fecha, turno, horas, es_finde) 
            VALUES (152, 'Godoy Maria', '2026-06-05', 'N_Planta', 12, 0)
        """)
        print("Insertada Godoy Maria el 05/06/2026")
        
        cursor.execute("""
            INSERT INTO guardias (cronograma_id, nombre, fecha, turno, horas, es_finde) 
            VALUES (152, 'Godoy Maria', '2026-06-27', 'N_Planta', 12, 1)
        """)
        print("Insertada Godoy Maria el 27/06/2026")
        
        # Barloa Matías Damián
        cursor.execute("""
            INSERT INTO guardias (cronograma_id, nombre, fecha, turno, horas, es_finde) 
            VALUES (152, 'Barloa Mat\u00edas Dami\u00e1n', '2026-06-16', 'N_Planta', 12, 0)
        """)
        print("Insertado Barloa Mat\u00edas Dami\u00e1n el 16/06/2026")
        
        cursor.execute("""
            INSERT INTO guardias (cronograma_id, nombre, fecha, turno, horas, es_finde) 
            VALUES (152, 'Barloa Mat\u00edas Dami\u00e1n', '2026-06-26', 'N_Planta', 12, 0)
        """)
        print("Insertado Barloa Mat\u00edas Dami\u00e1n el 26/06/2026")
        
        conn.commit()
        print("\n[OK] Asignaciones guardadas con éxito en la base de datos.")
    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] Ocurrió un error al insertar: {e}")
        
    conn.close()

if __name__ == '__main__':
    main()
