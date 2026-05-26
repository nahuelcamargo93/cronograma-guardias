import sqlite3

def check_history():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    # 1. Total historical hours per person
    print("=== HISTORICAL HOURS (aprobados, before 2026-07-01) ===")
    cursor.execute("""
        SELECT g.nombre, SUM(g.horas)
        FROM guardias g
        JOIN cronogramas c ON g.cronograma_id = c.id
        WHERE g.fecha < '2026-07-01' AND c.estado = 'aprobado'
        GROUP BY g.nombre
        ORDER BY SUM(g.horas) DESC
        LIMIT 10
    """)
    for row in cursor.fetchall():
        print(row)
        
    # 2. Check details for DOMINGUEZ VERONICA
    print("\n=== DETAILS FOR DOMINGUEZ VERONICA ===")
    cursor.execute("""
        SELECT c.id, c.fecha_inicio, c.fecha_fin, c.estado, SUM(g.horas)
        FROM guardias g
        JOIN cronogramas c ON g.cronograma_id = c.id
        WHERE g.nombre = 'DOMINGUEZ VERONICA'
        GROUP BY c.id
    """)
    for row in cursor.fetchall():
        print(f"Cronograma ID: {row[0]}, Period: {row[1]} to {row[2]}, Status: {row[3]}, Hours: {row[4]}")
        
    conn.close()

if __name__ == '__main__':
    check_history()
