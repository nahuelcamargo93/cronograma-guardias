import sqlite3

def main():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    # 1. Find duplicates
    print("=== BUSCANDO DUPLICADOS EN GUARDIAS ===")
    duplicates = cursor.execute("""
        SELECT cronograma_id, nombre, fecha, turno, COUNT(*) 
        FROM guardias 
        GROUP BY cronograma_id, nombre, fecha, turno
        HAVING COUNT(*) > 1
    """).fetchall()
    
    if not duplicates:
        print("No se encontraron filas duplicadas.")
    else:
        for d in duplicates:
            print(f"Crono: {d[0]} | Nombre: {d[1]} | Fecha: {d[2]} | Turno: {d[3]} | Cantidad: {d[4]}")
            
        # 2. Delete duplicates keeping the lowest rowid
        cursor.execute("""
            DELETE FROM guardias
            WHERE rowid NOT IN (
                SELECT MIN(rowid)
                FROM guardias
                GROUP BY cronograma_id, nombre, fecha, turno
            )
        """)
        conn.commit()
        print(f"\n[OK] Duplicados eliminados. Filas afectadas: {conn.total_changes}")
        
    conn.close()

if __name__ == '__main__':
    main()
