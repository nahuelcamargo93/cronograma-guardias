import sqlite3
from datetime import datetime, date, timedelta

DB_PATH = "cronograma_inteligente.db"
CRONOGRAMA_ID = 378

def get_dates_in_range(start_date, end_date):
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)
    curr = start
    dates = []
    while curr <= end:
        dates.append(curr)
        curr += timedelta(days=1)
    return dates

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT fecha_inicio, fecha_fin FROM cronogramas WHERE id = ?", (CRONOGRAMA_ID,))
    fecha_inicio, fecha_fin = cursor.fetchone()
    fechas_mes = get_dates_in_range(fecha_inicio, fecha_fin)

    cursor.execute("SELECT DISTINCT nombre FROM guardias WHERE cronograma_id = ?", (CRONOGRAMA_ID,))
    personal_nombres = [r[0] for r in cursor.fetchall()]

    # Mapear días con licencias tratadas como francos (solo excluimos TRABAJO y FLR)
    calendario_con_licencias = {}
    for nombre in personal_nombres:
        calendario_con_licencias[nombre] = {f: 'FRANCO_O_LICENCIA' for f in fechas_mes}

    # Cargar Guardias (Trabajo)
    cursor.execute("SELECT nombre, fecha FROM guardias WHERE cronograma_id = ?", (CRONOGRAMA_ID,))
    for nombre, fecha_str in cursor.fetchall():
        f = date.fromisoformat(fecha_str)
        if f in calendario_con_licencias[nombre]:
            calendario_con_licencias[nombre][f] = 'TRABAJO'

    # Cargar FLR
    cursor.execute("SELECT nombre, fecha_inicio, fecha_fin FROM flr_asignados WHERE cronograma_id = ?", (CRONOGRAMA_ID,))
    for nombre, flr_ini, flr_fin in cursor.fetchall():
        if nombre in calendario_con_licencias:
            ini = date.fromisoformat(flr_ini)
            fin = date.fromisoformat(flr_fin)
            curr = ini
            while curr <= fin:
                if curr in calendario_con_licencias[nombre]:
                    calendario_con_licencias[nombre][curr] = 'FLR'
                curr += timedelta(days=1)

    # Agrupar semanas
    semanas = {}
    for f in fechas_mes:
        iso_year, iso_week, _ = f.isocalendar()
        key = (iso_year, iso_week)
        if key not in semanas:
            semanas[key] = []
        semanas[key].append(f)

    print("--- ANÁLISIS TRATANDO LAS LICENCIAS COMO FRANCOS ---")
    
    # Francos por semana (incluyendo licencias, sin FLR)
    for completa_only in [False, True]:
        tipo_analisis = "SEMANAS COMPLETAS EN EL MES" if completa_only else "TODAS LAS SEMANAS"
        emp_mas_4 = set()
        for (y, w), days in semanas.items():
            if completa_only and len(days) < 7:
                continue
            for nombre in personal_nombres:
                francos = sum(1 for f in days if calendario_con_licencias[nombre][f] == 'FRANCO_O_LICENCIA')
                if francos > 4:
                    emp_mas_4.add(nombre)
                    print(f"  - {nombre}: Año {y} Sem {w} -> {francos} francos/licencias (sin contar FLR)")
        print(f"Con {tipo_analisis}: {len(emp_mas_4)} enfermeros con > 4 francos/licencias en una semana")

    # Consecutivos (incluyendo licencias, sin FLR)
    emp_consecutivos = {}
    for nombre in personal_nombres:
        racha_actual = []
        rachas_encontradas = []
        for f in fechas_mes:
            estado = calendario_con_licencias[nombre][f]
            if estado == 'FRANCO_O_LICENCIA':
                racha_actual.append(f)
            else:
                if len(racha_actual) >= 4:
                    rachas_encontradas.append(list(racha_actual))
                racha_actual = []
        if len(racha_actual) >= 4:
            rachas_encontradas.append(list(racha_actual))
        if rachas_encontradas:
            emp_consecutivos[nombre] = rachas_encontradas

    print(f"\nCantidad de enfermeros con >= 4 días consecutivos de Franco/Licencia: {len(emp_consecutivos)}")
    for nombre, rachas in sorted(emp_consecutivos.items()):
        desc = [f"desde {r[0]} hasta {r[-1]} ({len(r)} días)" for r in rachas]
        print(f"  - {nombre}: {', '.join(desc)}")

    conn.close()

if __name__ == "__main__":
    main()
