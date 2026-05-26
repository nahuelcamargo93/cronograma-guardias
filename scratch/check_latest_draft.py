import sqlite3

def run_diag():
    conn = sqlite3.connect("cronograma_inteligente.db")
    conn.row_factory = sqlite3.Row
    
    # Get the latest cronograma id for service 2
    row = conn.execute("""
        SELECT MAX(c.id) as max_id
        FROM cronogramas c
        JOIN guardias g ON g.cronograma_id = c.id
        JOIN personal p ON g.nombre = p.nombre
        WHERE p.servicio_id = 2
    """).fetchone()
    
    max_id = row['max_id']
    if not max_id:
        print("No se encontraron cronogramas para enfermería.")
        conn.close()
        return
        
    print(f"Último cronograma para Enfermería (ID: {max_id}):")
    g_rows = conn.execute("""
        SELECT fecha, turno, horas
        FROM guardias
        WHERE cronograma_id = ? AND nombre = 'ABELENDA GRISELL'
        ORDER BY fecha
    """, (max_id,)).fetchall()
    
    for gr in g_rows:
        print(f"Fecha: {gr['fecha']} | Turno: {gr['turno']} | Horas: {gr['horas']}")
        
    conn.close()

if __name__ == '__main__':
    run_diag()
