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

    # 1. Obtener detalles del cronograma
    cursor.execute("SELECT fecha_inicio, fecha_fin FROM cronogramas WHERE id = ?", (CRONOGRAMA_ID,))
    row = cursor.fetchone()
    if not row:
        print("Cronograma no encontrado.")
        return
    fecha_inicio, fecha_fin = row
    print(f"Analizando cronograma {CRONOGRAMA_ID} desde {fecha_inicio} hasta {fecha_fin}")

    fechas_mes = get_dates_in_range(fecha_inicio, fecha_fin)
    fechas_str_set = {f.isoformat() for f in fechas_mes}

    # 2. Obtener lista de personal que trabajó en este cronograma (Enfermeros)
    cursor.execute("""
        SELECT DISTINCT nombre FROM guardias WHERE cronograma_id = ?
    """, (CRONOGRAMA_ID,))
    personal_nombres = [r[0] for r in cursor.fetchall()]
    print(f"Total personal con guardias asignadas en el cronograma: {len(personal_nombres)}")

    # 3. Mapear cada día del mes para cada empleado
    # Tipos de día: 'TRABAJO', 'LICENCIA', 'FLR', 'FRANCO'
    calendario_emp = {}
    for nombre in personal_nombres:
        calendario_emp[nombre] = {}
        for f in fechas_mes:
            calendario_emp[nombre][f] = 'FRANCO'

    # A. Cargar Guardias (Trabajo)
    cursor.execute("""
        SELECT nombre, fecha FROM guardias 
        WHERE cronograma_id = ?
    """, (CRONOGRAMA_ID,))
    for nombre, fecha_str in cursor.fetchall():
        try:
            f = date.fromisoformat(fecha_str)
            if f in calendario_emp[nombre]:
                calendario_emp[nombre][f] = 'TRABAJO'
        except KeyError:
            pass

    # B. Cargar Licencias
    cursor.execute("""
        SELECT nombre, fecha_inicio, fecha_fin FROM licencias
    """)
    for nombre, lic_ini, lic_fin in cursor.fetchall():
        if nombre in calendario_emp:
            try:
                ini = date.fromisoformat(lic_ini)
                fin = date.fromisoformat(lic_fin)
                # Marcar los días de licencia que caen en el mes
                curr = ini
                while curr <= fin:
                    if curr in calendario_emp[nombre] and calendario_emp[nombre][curr] != 'TRABAJO':
                        calendario_emp[nombre][curr] = 'LICENCIA'
                    curr += timedelta(days=1)
            except ValueError:
                pass

    # C. Cargar FLR Asignados
    cursor.execute("""
        SELECT nombre, fecha_inicio, fecha_fin FROM flr_asignados
        WHERE cronograma_id = ?
    """, (CRONOGRAMA_ID,))
    for nombre, flr_ini, flr_fin in cursor.fetchall():
        if nombre in calendario_emp:
            try:
                ini = date.fromisoformat(flr_ini)
                fin = date.fromisoformat(flr_fin)
                curr = ini
                while curr <= fin:
                    if curr in calendario_emp[nombre]:
                        # Si coincide con FLR, se marca como FLR
                        calendario_emp[nombre][curr] = 'FLR'
                    curr += timedelta(days=1)
            except ValueError:
                pass

    # 4. Agrupar fechas del mes por semanas ISO
    # Una semana ISO es de lunes a domingo.
    semanas = {}
    for f in fechas_mes:
        iso_year, iso_week, _ = f.isocalendar()
        key = (iso_year, iso_week)
        if key not in semanas:
            semanas[key] = []
        semanas[key].append(f)

    print("\nSemanas identificadas en el rango del mes:")
    for (y, w), days in sorted(semanas.items()):
        print(f"  Año {y}, Semana {w}: {len(days)} días en el mes (desde {days[0]} hasta {days[-1]})")

    # 5. Analizar pregunta 1: Cuantos enfermeros tienen mas de 4 dias de franco en una misma semana (sin contar FLR)
    # Mostraremos los resultados de dos formas:
    # A) Considerando todas las semanas (incluso las incompletas en los bordes del mes).
    # B) Considerando únicamente las semanas completas de 7 días dentro del mes.
    print("\n--- ANÁLISIS DE FRANCOS POR SEMANA (MÁS DE 4 DÍAS DE FRANCO) ---")
    
    for completa_only in [False, True]:
        tipo_analisis = "SEMANAS COMPLETAS DE 7 DÍAS EN EL MES" if completa_only else "TODAS LAS SEMANAS (INCLUYENDO INCOMPLETAS)"
        print(f"\nAnalizando: {tipo_analisis}")
        
        emp_mas_de_4_francos = set()
        detalles_semanas = []
        
        for (y, w), days in sorted(semanas.items()):
            if completa_only and len(days) < 7:
                continue
                
            for nombre in personal_nombres:
                francos_en_semana = 0
                flr_en_semana = 0
                trabajo_en_semana = 0
                licencia_en_semana = 0
                for f in days:
                    estado = calendario_emp[nombre][f]
                    if estado == 'FRANCO':
                        francos_en_semana += 1
                    elif estado == 'FLR':
                        flr_en_semana += 1
                    elif estado == 'TRABAJO':
                        trabajo_en_semana += 1
                    elif estado == 'LICENCIA':
                        licencia_en_semana += 1
                
                if francos_en_semana > 4:
                    emp_mas_de_4_francos.add(nombre)
                    detalles_semanas.append((nombre, y, w, francos_en_semana, flr_en_semana, trabajo_en_semana, licencia_en_semana))
        
        print(f"Cantidad de enfermeros con > 4 francos en una misma semana: {len(emp_mas_de_4_francos)}")
        if emp_mas_de_4_francos:
            print("Enfermeros y detalles por semana:")
            for nombre, y, w, fr, flr, tr, lic in sorted(detalles_semanas):
                print(f"  - {nombre}: Año {y} Sem {w} -> {fr} Francos (FLR={flr}, Trabajo={tr}, Licencia={lic})")

    # 6. Analizar pregunta 2: Cuantos enfermeros tienen 4 dias consecutivos de Franco (sin contar FLR)
    print("\n--- ANÁLISIS DE FRANCOS CONSECUTIVOS (MÍNIMO 4 DÍAS SEGUIDOS) ---")
    emp_consecutivos = {}
    
    for nombre in personal_nombres:
        racha_actual = []
        rachas_encontradas = []
        for f in fechas_mes:
            estado = calendario_emp[nombre][f]
            if estado == 'FRANCO':
                racha_actual.append(f)
            else:
                if len(racha_actual) >= 4:
                    rachas_encontradas.append(list(racha_actual))
                racha_actual = []
        if len(racha_actual) >= 4:
            rachas_encontradas.append(list(racha_actual))
            
        if rachas_encontradas:
            emp_consecutivos[nombre] = rachas_encontradas

    print(f"Cantidad de enfermeros con 4 o más días consecutivos de Franco: {len(emp_consecutivos)}")
    if emp_consecutivos:
        print("Enfermeros y sus rachas de francos consecutivos:")
        for nombre, rachas in sorted(emp_consecutivos.items()):
            rachas_desc = []
            for r in rachas:
                rachas_desc.append(f"desde {r[0]} hasta {r[-1]} ({len(r)} días)")
            print(f"  - {nombre}: {', '.join(rachas_desc)}")

    # 7. Detalles específicos adicionales: verificar si hay enfermeros con exactamente 4 días de franco consecutivos
    print("\n--- ANÁLISIS DE EXACTAMENTE 4 DÍAS CONSECUTIVOS DE FRANCO ---")
    emp_exactos_4 = {}
    for nombre, rachas in emp_consecutivos.items():
        rachas_4 = [r for r in rachas if len(r) == 4]
        if rachas_4:
            emp_exactos_4[nombre] = rachas_4
    print(f"Cantidad de enfermeros con rachas de EXACTAMENTE 4 días consecutivos de Franco: {len(emp_exactos_4)}")
    for nombre, rachas in sorted(emp_exactos_4.items()):
        rachas_desc = [f"desde {r[0]} hasta {r[-1]}" for r in rachas]
        print(f"  - {nombre}: {', '.join(rachas_desc)}")

    conn.close()

if __name__ == "__main__":
    main()
