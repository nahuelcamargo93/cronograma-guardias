import sqlite3
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import get_connection

def inspect():
    conn = get_connection()
    last_cr = conn.execute("SELECT id, fecha_inicio, fecha_fin FROM cronogramas ORDER BY id DESC LIMIT 1").fetchone()
    if not last_cr:
        print("No cronogramas found.")
        return
    cr_id, fi, ff = last_cr
    print(f"Cronograma ID: {cr_id} ({fi} to {ff})")
    
    # Let's query all monitorista assignments per day and shift
    rows = conn.execute("""
        SELECT g.fecha, g.turno, COUNT(*) as cant
        FROM guardias g
        JOIN personal p ON g.nombre = p.nombre
        WHERE g.cronograma_id = ? AND p.rol = 'Monitorista' AND p.servicio_id = 4
        GROUP BY g.fecha, g.turno
        ORDER BY g.fecha, g.turno
    """, (cr_id,)).fetchall()
    
    # We want to see it as a table: Fecha, DayOfWeek, 00-06_Mon, 06-12_Mon, 12-18_Mon, 18-24_Mon, Total
    import pandas as pd
    data = {}
    for r in rows:
        fecha, turno, cant = r
        # Extract turn category: '00-06', '06-12', '12-18', '18-24'
        t_cat = turno.split('_')[0]
        data.setdefault(fecha, {})[t_cat] = cant
        
    df_data = []
    dias_nombres = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    for fecha in sorted(data.keys()):
        dt = pd.to_datetime(fecha)
        dow = dias_nombres[dt.weekday()]
        shifts = data[fecha]
        df_data.append({
            'Fecha': fecha,
            'Día': dow,
            '00-06': shifts.get('00-06', 0),
            '06-12': shifts.get('06-12', 0),
            '12-18': shifts.get('12-18', 0),
            '18-24': shifts.get('18-24', 0),
            'Total': sum(shifts.values())
        })
        
    df = pd.DataFrame(df_data)
    print(df.to_string(index=False))

if __name__ == "__main__":
    inspect()
