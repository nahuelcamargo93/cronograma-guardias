import sqlite3

def run():
    conn = sqlite3.connect("cronograma_inteligente.db")
    conn.row_factory = sqlite3.Row
    
    print("=== NOMBRES ASIGNADOS EN EL CRONOGRAMA 118 ===")
    names = conn.execute("SELECT DISTINCT nombre FROM guardias WHERE cronograma_id = 118 ORDER BY nombre").fetchall()
    for n in names:
        print(n['nombre'])
        
    print("\n=== COINCIDENCIAS CON GRISELL EN PERSONAL ===")
    p_rows = conn.execute("SELECT nombre FROM personal WHERE nombre LIKE '%Grisell%' OR nombre LIKE '%Abelanda%'").fetchall()
    for pr in p_rows:
        print(pr['nombre'])
        
    conn.close()

if __name__ == '__main__':
    run()
