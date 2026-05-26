import sqlite3
from datetime import datetime, date, timedelta

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
        
    print(f"Analizando mezclas de turnos en Cronograma ID: {max_id}")
    
    # Load all guardias
    g_rows = conn.execute("""
        SELECT nombre, fecha, turno
        FROM guardias
        WHERE cronograma_id = ?
        ORDER BY nombre, fecha
    """, (max_id,)).fetchall()
    
    # Group by name and week
    fecha_inicio_dt = date.fromisoformat("2026-07-01")
    guardias_by_emp = {}
    for r in g_rows:
        name = r['nombre']
        fecha = date.fromisoformat(r['fecha'])
        turno = r['turno']
        
        # Calculate week (Lunes-Domingo)
        lunes = fecha - timedelta(days=fecha.weekday())
        week_key = lunes.isoformat()
        
        guardias_by_emp.setdefault(name, {}).setdefault(week_key, []).append((r['fecha'], turno))
        
    mix_count = 0
    total_weeks = 0
    for name, weeks in guardias_by_emp.items():
        for week_key, guards in weeks.items():
            total_weeks += 1
            turnos_in_week = set()
            for f, t in guards:
                if t in ['M', 'MT']:
                    turnos_in_week.add('M')
                if t in ['T', 'MT']:
                    turnos_in_week.add('T')
                if t in ['TN', 'TNN']:
                    turnos_in_week.add('TN')
                if t in ['N', 'TNN']:
                    turnos_in_week.add('N')
            
            if len(turnos_in_week) > 1:
                mix_count += 1
                if mix_count <= 10:
                    print(f"Empleado: {name} | Semana: {week_key} | Turnos distintos: {list(turnos_in_week)}")
                    for f, t in sorted(guards):
                        print(f"  {f}: {t}")
                        
    print(f"\nTotal semanas analizadas: {total_weeks}")
    print(f"Total semanas con mezcla: {mix_count}")
    conn.close()

if __name__ == '__main__':
    run_diag()
