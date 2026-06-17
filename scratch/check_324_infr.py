import sqlite3

db_path = "cronograma_inteligente.db"

def inspect():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Obtener el último cronograma
    cursor.execute("SELECT MAX(id) FROM cronogramas")
    last_id = cursor.fetchone()[0]
    
    print(f"Último Cronograma ID: {last_id}")
    
    # Infracciones
    cursor.execute("""
        SELECT codigo_regla, detalle 
        FROM infracciones_debug 
        WHERE cronograma_id = ?
    """, (last_id,))
    rows = cursor.fetchall()
    print(f"Infracciones para el cronograma {last_id}: {len(rows)}")
    for r in rows:
        print(f"  Regla: {r[0]}, Detalle: {r[1]}")
        
    # Y para el 324 específicamente
    print(f"\nInfracciones para el cronograma 324:")
    cursor.execute("""
        SELECT codigo_regla, detalle 
        FROM infracciones_debug 
        WHERE cronograma_id = 324
    """)
    rows324 = cursor.fetchall()
    for r in rows324:
        print(f"  Regla: {r[0]}, Detalle: {r[1]}")
        
    conn.close()

if __name__ == "__main__":
    inspect()
