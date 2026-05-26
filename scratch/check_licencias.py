import sqlite3

def run():
    conn = sqlite3.connect("cronograma_inteligente.db")
    conn.row_factory = sqlite3.Row
    
    rows = conn.execute("""
        SELECT nombre, fecha_inicio, fecha_fin, tipo
        FROM licencias
        WHERE (fecha_inicio <= '2026-07-31' AND fecha_fin >= '2026-07-01')
        ORDER BY nombre, fecha_inicio
    """).fetchall()
    
    print(f"Total licencias que solapan con julio 2026: {len(rows)}")
    for r in rows:
        print(f"  Nombre: {r['nombre']} | Inicio: {r['fecha_inicio']} | Fin: {r['fecha_fin']} | Tipo: {r['tipo']}")
        
    conn.close()

if __name__ == '__main__':
    run()
