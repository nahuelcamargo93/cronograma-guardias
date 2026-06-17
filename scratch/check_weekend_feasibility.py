import sqlite3
import datetime
from datetime import date, timedelta

conn = sqlite3.connect("cronograma_inteligente.db")
crono_id = 438

# Check Toledo, Andrea's weekday assignments in the original crono 438
# We want to see her weekly hours and if she has room for a weekend shift
fecha_inicio = "2026-06-22"
fecha_fin = "2026-07-31"
fecha_inicio_dt = date.fromisoformat(fecha_inicio)

# Let's group her guards by week
from restricciones.hard._utils import get_semanas_calendario
dias_del_bloque = (date.fromisoformat(fecha_fin) - fecha_inicio_dt).days + 1
semanas = get_semanas_calendario(dias_del_bloque, fecha_inicio_dt)

# Load Toledo Andrea's guards
guards = conn.execute("SELECT fecha, turno, horas FROM guardias WHERE cronograma_id = ? AND nombre = 'Toledo, Andrea'", (crono_id,)).fetchall()
guards_by_date = {g[0]: (g[1], g[2]) for g in guards}

print("=== TOLEDO, ANDREA: GUARDAS Y HORAS POR SEMANA ===")
for (iso_y, iso_w), days in semanas.items():
    print(f"\nSemana {iso_y}-W{iso_w}:")
    week_hours = 0
    weekday_hours = 0
    for d, dt_val in days:
        dt_str = dt_val.isoformat()
        is_w = dt_val.weekday() in (5, 6)
        if dt_str in guards_by_date:
            t_name, hs = guards_by_date[dt_str]
            print(f"  {dt_str} ({dt_val.strftime('%a')}): {t_name} ({hs} hs)")
            week_hours += hs
            if not is_w:
                weekday_hours += hs
        else:
            # print(f"  {dt_str} ({dt_val.strftime('%a')}): LIBRE")
            pass
    print(f"  Total Horas Semana: {week_hours} hs (Weekday: {weekday_hours} hs)")
    
    # Check if we could add Dia_UCO (12 hs) on Saturday or Sunday of this week
    # Saturday is days[-2], Sunday is days[-1]
    sat_dt = days[-2][1]
    sun_dt = days[-1][1]
    
    # Sat/Sun UCO demand config: Dia_UCO (12 hs)
    # Check if adding Dia_UCO to Saturday violates MAX_HORAS_SEMANA (42)
    if weekday_hours + 12 <= 42:
        print(f"  -> Posible Sabado {sat_dt.isoformat()}: SI (Suma: {weekday_hours + 12} hs)")
    else:
        print(f"  -> Posible Sabado {sat_dt.isoformat()}: NO (Supera 42 hs: {weekday_hours + 12} hs)")
        
    if weekday_hours + 12 <= 42:
        print(f"  -> Posible Domingo {sun_dt.isoformat()}: SI (Suma: {weekday_hours + 12} hs)")
    else:
        print(f"  -> Posible Domingo {sun_dt.isoformat()}: NO (Supera 42 hs: {weekday_hours + 12} hs)")

conn.close()
