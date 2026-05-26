import sqlite3

def run():
    conn = sqlite3.connect("cronograma_inteligente.db")
    conn.row_factory = sqlite3.Row
    
    print("=== ASSIGNMENTS FOR CRONOGRAMA 118 ===")
    g_rows = conn.execute("""
        SELECT g.nombre, g.fecha, g.turno, g.horas
        FROM guardias g
        WHERE g.cronograma_id = 118
        ORDER BY g.nombre, g.fecha
    """).fetchall()
    
    by_nurse = {}
    for r in g_rows:
        by_nurse.setdefault(r['nombre'], []).append(r)
        
    print(f"Total assignments: {len(g_rows)}")
    
    # Let's inspect ABELENDA GRISELL specifically
    print("\n=== ABELENDA GRISELL ASSIGNMENTS ===")
    gr_list = by_nurse.get('ABELENDA GRISELL', [])
    for gr in gr_list:
        print(f"Fecha: {gr['fecha']} | Turno: {gr['turno']} | Horas: {gr['horas']}")
        
    # Let's check how weeks are counted in reportes/enfermeria.py
    # Let's see the week-by-week assignments for ABELENDA GRISELL
    # We can group them by calendar week (Lunes-Domingo)
    from datetime import date, timedelta
    weeks = {}
    for gr in gr_list:
        dt = date.fromisoformat(gr['fecha'])
        lunes = dt - timedelta(days=dt.weekday())
        lunes_str = lunes.isoformat()
        weeks.setdefault(lunes_str, []).append(gr['turno'])
        
    print("\n=== ABELANDA GRISELL WEEKLY SHIFT MIX ===")
    for w, turnos in sorted(weeks.items()):
        print(f"Week starting {w}: {turnos}")

    conn.close()

if __name__ == '__main__':
    run()
