import sqlite3

def main():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    rows = cursor.execute("""
        SELECT * FROM infracciones_debug WHERE cronograma_id = 261
    """).fetchall()
    
    print("=== INFRACCIONES DE CRONOGRAMA 261 ===")
    if not rows:
        print("No hay infracciones para el cronograma 261 (se resolvió sin modo debug o sin violaciones).")
    for r in rows:
        print(f"Regla: {r[1]}, Detalle: {r[2]}")
        
    # Check if there are other cronogramas for service 2 and their status
    print("\n=== CRONOGRAMAS SERVICIO 2 ===")
    c_rows = cursor.execute("""
        SELECT c.id, c.fecha_inicio, c.fecha_fin, c.notas, c.estado, 
               (SELECT count(*) FROM guardias g WHERE g.cronograma_id = c.id) as cant_guardias,
               (SELECT count(*) FROM infracciones_debug i WHERE i.cronograma_id = c.id) as cant_infracciones
        FROM cronogramas c
        JOIN guardias g ON c.id = g.cronograma_id
        JOIN personal p ON g.nombre = p.nombre
        WHERE p.servicio_id = 2
        GROUP BY c.id
        ORDER BY c.id DESC
        LIMIT 10
    """).fetchall()
    for r in c_rows:
        print(f"ID: {r[0]}, Inicio: {r[1]}, Fin: {r[2]}, Notas: {r[3]}, Estado: {r[4]}, Guardias: {r[5]}, Infracciones: {r[6]}")
        
    conn.close()

if __name__ == '__main__':
    main()
