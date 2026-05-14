import sqlite3
from datetime import date, timedelta

def debug_necesarias():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    fecha_inicio_dt = date.fromisoformat("2026-05-25")
    feriados = ["2026-05-25"]
    offset_dia = fecha_inicio_dt.weekday()

    # 1. Cargar turnos desde DB (tal cual lo hace db.py)
    rows = cursor.execute("SELECT nombre, vacantes_semana, vacantes_finde FROM turnos_config WHERE servicio_id = 1").fetchall()
    config_turnos = {"Semana": {}, "Finde_Feriado": {}}
    for nombre, v_sem, v_fin in rows:
        config_turnos["Semana"][nombre] = v_sem
        config_turnos["Finde_Feriado"][nombre] = v_fin

    # 2. Cargar ajustes
    rows_ajustes = cursor.execute("""
        SELECT ta.fecha_inicio, ta.fecha_fin, tc.nombre, ta.vacantes
        FROM turnos_ajustes ta
        JOIN turnos_config tc ON ta.turno_config_id = tc.id
    """).fetchall()
    ajustes = {}
    for fi, ff, nombre, vac in rows_ajustes:
        ajustes.setdefault((fi, ff), {})[nombre] = vac

    print(f"{'Día':<12} | {'Turno':<15} | {'Vac':<5} | {'Horas':<5} | {'Total':<5}")
    print("-" * 50)

    # Analizar Semana 1 (del día 7 al 13)
    total_semana_1 = 0
    for d in range(7, 14):
        fecha_actual_dt = fecha_inicio_dt + timedelta(days=d)
        fecha_str = fecha_actual_dt.isoformat()
        es_f = (fecha_actual_dt.weekday() >= 5) or (fecha_str in feriados)
        tipo_dia = "Finde_Feriado" if es_f else "Semana"
        
        dia_total = 0
        for t_nombre, v_base in config_turnos[tipo_dia].items():
            vacantes = v_base
            # Aplicar ajuste
            for (fi, ff), cambios in ajustes.items():
                if fi <= fecha_str <= ff and t_nombre in cambios:
                    vacantes = cambios[t_nombre]
                    break
            
            if vacantes > 0:
                h = 12 if (es_f or t_nombre.startswith("Noche")) else 6
                subtotal = vacantes * h
                dia_total += subtotal
                print(f"{fecha_str} | {t_nombre:<15} | {vacantes:<5} | {h:<5} | {subtotal:<5}")
        
        print(f"{'':<12} | {'TOTAL DIA':<15} | {'':<5} | {'':<5} | {dia_total:<5}")
        print("-" * 50)
        total_semana_1 += dia_total

    print(f"\nTOTAL SEMANA 1: {total_semana_1} hs")
    conn.close()

if __name__ == "__main__":
    debug_necesarias()
